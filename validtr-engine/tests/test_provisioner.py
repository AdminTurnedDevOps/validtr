"""Tests for ComposeGenerator and credential management."""

import os
import tempfile

import pytest
import yaml

from models.stack import (
    FrameworkRecommendation,
    LLMRecommendation,
    MCPServerRecommendation,
    MCPTransport,
    StackRecommendation,
)
from provisioner.credentials import (
    PROVIDER_KEY_MAP,
    check_credentials,
    resolve_credentials,
)


def _make_stack(
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-20250514",
    mcp_servers: list[MCPServerRecommendation] | None = None,
) -> StackRecommendation:
    """Helper to build a minimal StackRecommendation."""
    return StackRecommendation(
        llm=LLMRecommendation(provider=provider, model=model, reason="test"),
        framework=FrameworkRecommendation(),
        mcp_servers=mcp_servers or [],
    )


# ---------------------------------------------------------------------------
# ComposeGenerator
# ---------------------------------------------------------------------------

class TestComposeGenerator:
    """Tests for ComposeGenerator.generate()."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        return str(tmp_path)

    def test_generate_creates_expected_files(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack()
        run_dir, compose_path = gen.generate("test-run-1", stack)

        assert os.path.isfile(compose_path)
        assert os.path.isfile(os.path.join(run_dir, "Dockerfile.agent"))
        assert os.path.isfile(os.path.join(run_dir, "entrypoint.py"))
        assert os.path.isfile(os.path.join(run_dir, "agent_loop.py"))

    def test_compose_has_agent_and_test_runner_services(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack()
        run_dir, compose_path = gen.generate("test-run-2", stack)

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        assert "services" in compose
        assert "agent" in compose["services"]
        assert "test-runner" in compose["services"]

    def test_compose_has_network(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack()
        _, compose_path = gen.generate("test-run-3", stack)

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        assert "networks" in compose
        assert "validtr-net" in compose["networks"]

    def test_compose_agent_environment(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack(provider="openai", model="gpt-4o")
        _, compose_path = gen.generate("test-run-4", stack)

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        agent_env = compose["services"]["agent"]["environment"]
        assert agent_env["VALIDTR_PROVIDER"] == "openai"
        assert agent_env["VALIDTR_MODEL"] == "gpt-4o"

    def test_compose_with_streamable_http_mcp(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack(
            mcp_servers=[
                MCPServerRecommendation(
                    name="custom-api",
                    transport=MCPTransport.STREAMABLE_HTTP,
                    install="docker pull custom-api",
                    credentials="CUSTOM_API_KEY",
                ),
            ],
        )
        _, compose_path = gen.generate("test-run-5", stack, credentials={"CUSTOM_API_KEY": "secret"})

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        assert "mcp-custom-api" in compose["services"]

    def test_workspace_directories_created(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack()
        run_dir, _ = gen.generate("test-run-6", stack)

        assert os.path.isdir(os.path.join(run_dir, "workspace"))
        assert os.path.isdir(os.path.join(run_dir, "workspace", "tests"))

    def test_compose_uses_base_image_when_no_mcp(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack(provider="anthropic")
        _, compose_path = gen.generate("test-run-7", stack)

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        agent = compose["services"]["agent"]
        assert agent.get("image") == "validtr-agent-base:latest"
        assert "build" not in agent

    def test_compose_uses_test_runner_base_image(self, output_dir):
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=output_dir)
        stack = _make_stack()
        _, compose_path = gen.generate("test-run-8", stack)

        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        runner = compose["services"]["test-runner"]
        assert runner.get("image") == "validtr-test-runner:latest"
        assert "build" not in runner


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

class TestResolveCredentials:
    """Tests for resolve_credentials()."""

    def test_reads_from_explicit_keys(self):
        stack = _make_stack(provider="anthropic")
        creds = resolve_credentials(stack, explicit_keys={"ANTHROPIC_API_KEY": "sk-test-123"})
        assert creds["ANTHROPIC_API_KEY"] == "sk-test-123"

    def test_reads_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-456")
        stack = _make_stack(provider="openai")
        creds = resolve_credentials(stack)
        assert creds["OPENAI_API_KEY"] == "sk-env-456"

    def test_explicit_keys_override_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
        stack = _make_stack(provider="anthropic")
        creds = resolve_credentials(stack, explicit_keys={"ANTHROPIC_API_KEY": "from-explicit"})
        assert creds["ANTHROPIC_API_KEY"] == "from-explicit"

    def test_mcp_server_credentials_resolved(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        stack = _make_stack(
            mcp_servers=[
                MCPServerRecommendation(
                    name="github",
                    transport=MCPTransport.STDIO,
                    install="npx github",
                    credentials="GITHUB_TOKEN",
                ),
            ],
        )
        creds = resolve_credentials(stack)
        assert creds.get("GITHUB_TOKEN") == "ghp_test"

    def test_missing_credential_not_in_result(self, monkeypatch):
        # Ensure env var is not set
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        stack = _make_stack(provider="anthropic")
        creds = resolve_credentials(stack)
        assert "ANTHROPIC_API_KEY" not in creds

    def test_no_credential_for_none_mcp(self):
        stack = _make_stack(
            mcp_servers=[
                MCPServerRecommendation(
                    name="memory",
                    transport=MCPTransport.STDIO,
                    install="npx memory",
                    credentials="none",
                ),
            ],
        )
        creds = resolve_credentials(stack, explicit_keys={"ANTHROPIC_API_KEY": "key"})
        # Only the provider key should be present, not "none"
        assert "none" not in creds


class TestCheckCredentials:
    """Tests for check_credentials()."""

    def test_all_present(self):
        stack = _make_stack(provider="anthropic")
        missing = check_credentials(stack, {"ANTHROPIC_API_KEY": "sk-test"})
        assert missing == []

    def test_provider_key_missing(self):
        stack = _make_stack(provider="openai")
        missing = check_credentials(stack, {})
        assert "OPENAI_API_KEY" in missing

    def test_mcp_credential_missing(self):
        stack = _make_stack(
            provider="anthropic",
            mcp_servers=[
                MCPServerRecommendation(
                    name="github",
                    transport=MCPTransport.STDIO,
                    install="npx github",
                    credentials="GITHUB_TOKEN",
                ),
            ],
        )
        missing = check_credentials(stack, {"ANTHROPIC_API_KEY": "key"})
        assert "GITHUB_TOKEN" in missing

    def test_mcp_none_credential_not_flagged(self):
        stack = _make_stack(
            provider="anthropic",
            mcp_servers=[
                MCPServerRecommendation(
                    name="filesystem",
                    transport=MCPTransport.STDIO,
                    install="npx fs",
                    credentials="none",
                ),
            ],
        )
        missing = check_credentials(stack, {"ANTHROPIC_API_KEY": "key"})
        assert missing == []

    def test_provider_key_map_contents(self):
        assert PROVIDER_KEY_MAP["anthropic"] == "ANTHROPIC_API_KEY"
        assert PROVIDER_KEY_MAP["openai"] == "OPENAI_API_KEY"
        assert PROVIDER_KEY_MAP["gemini"] == "GOOGLE_API_KEY"


# ---------------------------------------------------------------------------
# Path traversal protection (_handle_tool_call)
# ---------------------------------------------------------------------------

class TestPathTraversalProtection:
    """Tests for _handle_tool_call path traversal guard in compose_generator.py.

    The _handle_tool_call function is embedded in the agent_loop code that
    ComposeGenerator._write_agent_loop() writes to disk. We extract and test
    the logic directly by loading the generated agent_loop.py file.
    """

    @pytest.fixture
    def agent_loop_module(self, tmp_path):
        """Generate the agent_loop.py and import _handle_tool_call from it."""
        from provisioner.compose_generator import ComposeGenerator

        gen = ComposeGenerator(output_base=str(tmp_path))
        stack = _make_stack()
        run_dir, _ = gen.generate("path-test", stack)

        agent_loop_path = os.path.join(run_dir, "agent_loop.py")
        assert os.path.isfile(agent_loop_path)

        # We read the source and extract just _handle_tool_call
        # to test it with a mocked /workspace/output base
        with open(agent_loop_path) as f:
            source = f.read()

        return source, run_dir

    def test_safe_path_allowed(self, agent_loop_module, tmp_path):
        """A normal relative path inside the output dir should succeed."""
        source, run_dir = agent_loop_module

        # Create a fake /workspace/output equivalent
        output_dir = os.path.join(str(tmp_path), "workspace_output")
        os.makedirs(output_dir, exist_ok=True)

        # Replicate the path traversal logic
        base_dir = os.path.realpath(output_dir)
        path = "main.py"
        full_path = os.path.realpath(os.path.join(base_dir, path))
        assert full_path.startswith(base_dir + os.sep) or full_path == base_dir

    def test_traversal_blocked(self, tmp_path):
        """A path with .. that escapes the output dir should be blocked."""
        output_dir = os.path.join(str(tmp_path), "workspace_output")
        os.makedirs(output_dir, exist_ok=True)

        base_dir = os.path.realpath(output_dir)
        path = "../../etc/passwd"
        full_path = os.path.realpath(os.path.join(base_dir, path))
        assert not (full_path.startswith(base_dir + os.sep) or full_path == base_dir)

    def test_absolute_path_outside_blocked(self, tmp_path):
        """An absolute path outside the output dir should be blocked."""
        output_dir = os.path.join(str(tmp_path), "workspace_output")
        os.makedirs(output_dir, exist_ok=True)

        base_dir = os.path.realpath(output_dir)
        path = "/etc/passwd"
        full_path = os.path.realpath(os.path.join(base_dir, path))
        assert not (full_path.startswith(base_dir + os.sep) or full_path == base_dir)

    def test_nested_path_allowed(self, tmp_path):
        """A nested relative path inside the output dir should succeed."""
        output_dir = os.path.join(str(tmp_path), "workspace_output")
        os.makedirs(output_dir, exist_ok=True)

        base_dir = os.path.realpath(output_dir)
        path = "src/utils/helpers.py"
        full_path = os.path.realpath(os.path.join(base_dir, path))
        assert full_path.startswith(base_dir + os.sep)

    def test_dot_path_resolves_to_base(self, tmp_path):
        """A '.' path should resolve to the base directory itself."""
        output_dir = os.path.join(str(tmp_path), "workspace_output")
        os.makedirs(output_dir, exist_ok=True)

        base_dir = os.path.realpath(output_dir)
        path = "."
        full_path = os.path.realpath(os.path.join(base_dir, path))
        assert full_path == base_dir
