# Architecture

`validtr` is split into two runtime components:

- Go CLI (`validtr-cli`): command UX and engine client.
- Python engine (`validtr-engine`): orchestration and runtime pipeline.

## Runtime Flow

```text
CLI (Go) -> Engine API (FastAPI) -> Pipeline Components -> Docker
```

Pipeline components:

- Task Analyzer
- Recommendation Engine
- Execution Engine
- Test Generator
- Scoring Engine
- Retry Controller

## Local-First Design

Everything runs on your machine:

- CLI process
- Engine process
- Docker containers
- Task artifacts and tests
