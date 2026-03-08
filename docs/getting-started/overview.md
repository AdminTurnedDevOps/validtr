# Overview

`validtr` is a CLI and engine for validating agentic task execution.

For each run, it:

1. Analyzes your task.
2. Recommends the best stack.
3. Executes inside Docker.
4. Generates tests from output.
5. Scores result quality.
6. Retries with stack adjustments if needed.

## Core Components

- `validtr-cli`: user-facing Go CLI.
- `validtr-engine`: Python FastAPI orchestration engine.
- `validtr-ui`: optional UI surface (currently minimal).
