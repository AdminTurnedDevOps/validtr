# Quickstart

## 1. Start the engine

```bash
cd validtr-engine
source .venv/bin/activate
uvicorn api.server:app --host 127.0.0.1 --port 4041
```

## 2. Run your first task

```bash
./validtr run "Build a FastAPI web app with JWT auth" --provider anthropic
```

## 3. Optional modes

```bash
# Compare providers
./validtr run "Build a REST API" --compare anthropic,openai,gemini

# Recommend only, no Docker execution
./validtr run "Automate PR reviews" --dry-run
```
