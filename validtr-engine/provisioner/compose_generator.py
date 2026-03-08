"""Generates Docker Compose configurations from StackRecommendations."""

import logging
import os
import tempfile

import yaml

from models.stack import MCPTransport, StackRecommendation

logger = logging.getLogger(__name__)


class ComposeGenerator:
    """Generates Docker Compose YAML and supporting files for a run."""

    def __init__(self, output_base: str | None = None):
        self.output_base = output_base or os.path.join(tempfile.gettempdir(), "validtr-runs")

    def generate(
        self,
        run_id: str,
        stack: StackRecommendation,
        credentials: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        """Generate Docker Compose config. Returns (run_dir, compose_file_path)."""
        run_dir = os.path.join(self.output_base, run_id)
        os.makedirs(run_dir, exist_ok=True)
        os.makedirs(os.path.join(run_dir, "workspace"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "workspace", "tests"), exist_ok=True)

        compose = self._build_compose(run_id, stack, run_dir, credentials or {})

        compose_path = os.path.join(run_dir, "docker-compose.yml")
        with open(compose_path, "w") as f:
            yaml.dump(compose, f, default_flow_style=False)

        # Write agent scripts (mounted as volumes at runtime, not baked into image)
        self._write_entrypoint(run_dir)
        self._write_agent_loop(run_dir, stack)

        logger.info("Generated compose config at %s", compose_path)
        return run_dir, compose_path

    def _build_compose(
        self,
        run_id: str,
        stack: StackRecommendation,
        run_dir: str,
        credentials: dict[str, str],
    ) -> dict:
        """Build the Docker Compose dictionary."""
        services = {}

        # Agent container
        agent_env = {
            "VALIDTR_RUN_ID": run_id,
            "VALIDTR_PROVIDER": stack.llm.provider,
            "VALIDTR_MODEL": stack.llm.model,
        }
        # Inject credentials
        for key, value in credentials.items():
            agent_env[key] = value

        # Build MCP install commands for the Dockerfile
        mcp_installs = []
        for server in stack.mcp_servers:
            if server.transport == MCPTransport.STDIO:
                mcp_installs.append(f"RUN {server.install} || true")

        agent_dockerfile = self._generate_agent_dockerfile(mcp_installs)
        dockerfile_path = os.path.join(run_dir, "Dockerfile.agent")
        with open(dockerfile_path, "w") as f:
            f.write(agent_dockerfile)

        # Use base image directly when no MCP servers, per-run build otherwise
        if mcp_installs:
            services["agent"] = {
                "build": {
                    "context": run_dir,
                    "dockerfile": "Dockerfile.agent",
                },
                "environment": agent_env,
                "volumes": [
                    f"{os.path.join(run_dir, 'workspace')}:/workspace",
                    f"{os.path.join(run_dir, 'entrypoint.py')}:/app/entrypoint.py:ro",
                    f"{os.path.join(run_dir, 'agent_loop.py')}:/app/agent_loop.py:ro",
                ],
                "networks": ["validtr-net"],
            }
        else:
            services["agent"] = {
                "image": "validtr-agent-base:latest",
                "environment": agent_env,
                "volumes": [
                    f"{os.path.join(run_dir, 'workspace')}:/workspace",
                    f"{os.path.join(run_dir, 'entrypoint.py')}:/app/entrypoint.py:ro",
                    f"{os.path.join(run_dir, 'agent_loop.py')}:/app/agent_loop.py:ro",
                ],
                "networks": ["validtr-net"],
            }

        # MCP server containers (streamable-http only)
        for server in stack.mcp_servers:
            if server.transport == MCPTransport.STREAMABLE_HTTP:
                service_name = f"mcp-{server.name}"
                services[service_name] = {
                    "image": f"mcp-{server.name}:latest",
                    "networks": ["validtr-net"],
                    "environment": {},
                }
                if server.credentials != "none" and server.credentials in credentials:
                    services[service_name]["environment"][server.credentials] = credentials[server.credentials]

        # Test runner container — uses pre-built base image
        services["test-runner"] = {
            "image": "validtr-test-runner:latest",
            "volumes": [
                f"{os.path.join(run_dir, 'workspace')}:/workspace:ro",
            ],
            "networks": ["validtr-net"],
            "depends_on": ["agent"],
        }

        return {
            "version": "3.8",
            "services": services,
            "networks": {
                "validtr-net": {"driver": "bridge"},
            },
        }

    def _generate_agent_dockerfile(self, mcp_installs: list[str]) -> str:
        """Generate the agent Dockerfile with MCP server installations."""
        template_path = os.path.join(
            os.path.dirname(__file__), "templates", "agent.Dockerfile"
        )
        with open(template_path) as f:
            template = f.read()

        # Replace the MCP install placeholder
        mcp_section = "\n".join(mcp_installs) if mcp_installs else "# No MCP servers to install"
        return template.replace("# MCP_INSTALL_COMMANDS placeholder", mcp_section)

    def _write_entrypoint(self, run_dir: str) -> None:
        """Write the agent container entrypoint script."""
        entrypoint = '''"""Agent container entrypoint."""
import json
import os
import sys

def main():
    run_id = os.environ.get("VALIDTR_RUN_ID", "unknown")
    print(f"[validtr] Starting agent for run {run_id}")

    # Read task definition from mounted workspace
    task_path = "/workspace/task.json"
    if not os.path.exists(task_path):
        print("[validtr] ERROR: No task.json found in /workspace")
        sys.exit(1)

    with open(task_path) as f:
        task = json.load(f)

    # Read stack config
    stack_path = "/workspace/stack.json"
    if not os.path.exists(stack_path):
        print("[validtr] ERROR: No stack.json found in /workspace")
        sys.exit(1)

    with open(stack_path) as f:
        stack = json.load(f)

    # Run the agent loop
    from agent_loop import run_agent
    run_agent(task, stack)

if __name__ == "__main__":
    main()
'''
        with open(os.path.join(run_dir, "entrypoint.py"), "w") as f:
            f.write(entrypoint)

    def _write_agent_loop(self, run_dir: str, stack: StackRecommendation) -> None:
        """Write the agent loop script that runs inside the container."""
        agent_loop = '''"""Simple tool-calling agent loop for validtr."""
import json
import os
import subprocess
import sys

def get_llm_client():
    """Initialize the LLM client based on environment."""
    provider = os.environ.get("VALIDTR_PROVIDER", "anthropic")
    model = os.environ.get("VALIDTR_MODEL", "claude-sonnet-4-20250514")

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        return client, model, provider
    elif provider == "openai":
        import openai
        client = openai.OpenAI()
        return client, model, provider
    elif provider == "gemini":
        from google import genai
        client = genai.Client()
        return client, model, provider
    else:
        raise ValueError(f"Unknown provider: {provider}")

def run_agent(task: dict, stack: dict):
    """Run the agent loop to completion."""
    client, model, provider = get_llm_client()

    system_prompt = f"""You are an AI agent tasked with completing a software engineering task.
You must produce working output files in /workspace/output/.

Task: {task.get('raw_input', '')}

Success Criteria:
{chr(10).join('- ' + c for c in task.get('success_criteria', []))}

Write all output files to /workspace/output/. Create the directory if it doesn't exist.
When done, write a manifest.json to /workspace/output/manifest.json listing all files you created."""

    os.makedirs("/workspace/output", exist_ok=True)

    # Simple agent loop (no MCP for Phase 1 — direct code generation)
    if provider == "anthropic":
        _run_anthropic_loop(client, model, system_prompt, task)
    elif provider == "openai":
        _run_openai_loop(client, model, system_prompt, task)
    elif provider == "gemini":
        _run_gemini_loop(client, model, system_prompt, task)

def _run_anthropic_loop(client, model, system_prompt, task):
    """Run agent loop with Anthropic."""
    tools = [
        {
            "name": "write_file",
            "description": "Write content to a file in /workspace/output/",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path within /workspace/output/"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "run_command",
            "description": "Run a shell command and return output",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                },
                "required": ["command"],
            },
        },
    ]

    messages = [{"role": "user", "content": f"Complete this task: {task.get('raw_input', '')}"}]

    for i in range(50):  # max 50 LLM calls
        response = client.messages.create(
            model=model,
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=4096,
        )

        # Process response
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            print("[validtr] Agent completed task")
            break

        # Handle tool calls
        tool_results = []
        for block in assistant_content:
            if block.type == "tool_use":
                result = _handle_tool_call(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

def _run_openai_loop(client, model, system_prompt, task):
    """Run agent loop with OpenAI."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file in /workspace/output/",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Run a shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                    },
                    "required": ["command"],
                },
            },
        },
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Complete this task: {task.get('raw_input', '')}"},
    ]

    for i in range(50):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=tools, max_tokens=4096,
        )
        choice = response.choices[0]
        messages.append(choice.message)

        if choice.finish_reason != "tool_calls":
            print("[validtr] Agent completed task")
            break

        for tc in choice.message.tool_calls or []:
            args = json.loads(tc.function.arguments)
            result = _handle_tool_call(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

def _run_gemini_loop(client, model, system_prompt, task):
    """Run agent loop with Gemini (simplified — no tool calling)."""
    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=[f"{system_prompt}\\n\\nTask: {task.get('raw_input', '')}\\n\\nGenerate all necessary code files. For each file, output it in this format:\\n--- FILE: path/to/file ---\\ncontent\\n--- END FILE ---"],
        config=types.GenerateContentConfig(max_output_tokens=8192),
    )

    # Parse file blocks from response
    text = response.text or ""
    import re
    file_blocks = re.findall(r'--- FILE: (.+?) ---\\n(.*?)\\n--- END FILE ---', text, re.DOTALL)
    for path, content in file_blocks:
        _handle_tool_call("write_file", {"path": path.strip(), "content": content})

    if not file_blocks:
        # Write raw output as a single file
        _handle_tool_call("write_file", {"path": "output.py", "content": text})

def _handle_tool_call(name: str, args: dict) -> str:
    """Handle a tool call from the agent."""
    if name == "write_file":
        path = args.get("path", "output.txt")
        content = args.get("content", "")
        base_dir = os.path.realpath("/workspace/output")
        full_path = os.path.realpath(os.path.join(base_dir, path))
        if not full_path.startswith(base_dir + os.sep) and full_path != base_dir:
            print(f"[validtr] BLOCKED path traversal attempt: {path}")
            return f"Error: path '{path}' escapes output directory"
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        print(f"[validtr] Wrote file: {path}")
        return f"File written: {path}"
    elif name == "run_command":
        command = args.get("command", "echo hello")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30,
                cwd="/workspace/output",
            )
            output = result.stdout + result.stderr
            return output[:2000]  # Truncate long output
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Command failed: {e}"
    else:
        return f"Unknown tool: {name}"
'''
        with open(os.path.join(run_dir, "agent_loop.py"), "w") as f:
            f.write(agent_loop)
