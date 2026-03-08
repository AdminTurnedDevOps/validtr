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

## Command Behavior Notes

- `run --dry-run` calls engine with `dry_run=true` and does not execute Docker workloads.
- `run --compare` runs each provider sequentially and skips providers with missing API keys.
- `run` and `run --compare` pass `TAVILY_API_KEY` to engine as `search_api_key` when present.
- CLI config values are used only if corresponding flags are not explicitly set.

## Global Flags

- `-c, --config`: override config path (default `~/.validtr/config.yaml`)

## Exit Behavior

The root command exits with code `1` on command error.
