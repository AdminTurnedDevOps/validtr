# Project Layout

This repository is a monorepo with three main directories.

## `validtr-cli`

Go CLI implemented with Cobra.

- `cmd/root.go`: root command and global `--config` flag.
- `cmd/run.go`: run, compare, and dry-run flows.
- `cmd/mcp.go`: MCP discovery commands.
- `cmd/config.go`: configuration commands.
- `internal/engine/client.go`: HTTP client to Python engine.
- `internal/config/*`: local YAML config and env-key resolution.

## `validtr-engine`

Python FastAPI engine and orchestration pipeline.

- `api/`: REST API routes.
- `analyzer/`: task classification and requirement extraction.
- `recommender/`: web search + MCP registry + skills registry + LLM reasoning.
- `executor/`: Docker runtime execution and trace capture.
- `provisioner/`: compose and runtime script generation.
- `test_generator/`: LLM-generated pytest + isolated test execution.
- `scorer/`: weighted scoring.
- `retry/`: retry decision and stack adjustment logic.
- `models/`: Pydantic schemas shared by pipeline stages.

## `validtr-ui`

UI placeholder directory (`src/`) is present but not currently implemented.
