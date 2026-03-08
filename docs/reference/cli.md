# CLI Reference

## run

```bash
./validtr run "Build a FastAPI web app with JWT auth" --provider anthropic
```

Flags:

- `--provider` provider name (`anthropic`, `openai`, `gemini`)
- `--compare` comma-separated providers for comparison mode
- `--dry-run` recommendation only (no execution)
- `--model` model override
- `--max-retries` retry limit
- `--score-threshold` passing threshold
- `--timeout` execution timeout in seconds

## mcp

```bash
./validtr mcp list
./validtr mcp search "kubernetes"
./validtr mcp info filesystem
```

## config

```bash
./validtr config set provider anthropic
./validtr config set score-threshold 90
./validtr config show
```
