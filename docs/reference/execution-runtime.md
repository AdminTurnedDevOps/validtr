# Execution Runtime

Execution behavior lives in `executor/*` and `provisioner/*`.

## Base Images

Auto-built once if missing:

- `validtr-agent-base:latest`
- `validtr-test-runner:latest`

Agent base image includes:

- Python 3.12
- Node.js 20
- SDKs: `anthropic`, `openai`, `google-genai`, `httpx`, `pydantic`

## Per-Run Files

`ComposeGenerator` creates run artifacts under temp storage (`/tmp/validtr-runs/<run_id>` by default):

- `docker-compose.yml`
- `Dockerfile.agent`
- `entrypoint.py`
- `agent_loop.py`
- `workspace/task.json`
- `workspace/stack.json`

## Agent Execution

- container mounts run workspace and scripts
- output files are expected under `/workspace/output`
- artifact collector reads files recursively from output directory

## Tooling in Agent Loop

Anthropic/OpenAI agent loops can call:

- `write_file(path, content)`
- `run_command(command)`

Gemini loop currently uses a simplified file-block parsing flow.

## Path Traversal Guard

`write_file` blocks writes that escape `/workspace/output` via realpath checks.

## Streamable HTTP MCP Services

For `streamable-http` MCP entries, compose creates sidecar services named `mcp-<server-name>`.
