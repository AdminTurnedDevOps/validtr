# Install

## Prerequisites

- Docker
- Python 3.12+
- Go 1.23+
- One provider API key:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY`

Optional web search key:

- `TAVILY_API_KEY`

## Build Engine

```bash
cd validtr-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build CLI

```bash
cd validtr-cli
go build -o ../validtr .
cd ..
```
