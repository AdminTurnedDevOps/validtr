# API Examples

Base URL:

```text
http://127.0.0.1:4041
```

## Health

```bash
curl http://127.0.0.1:4041/health
```

## Run Task

```bash
curl -X POST http://127.0.0.1:4041/api/run \
  -H 'content-type: application/json' \
  -d '{
    "task": "Build a FastAPI app with JWT auth",
    "provider": "anthropic",
    "api_key": "<provider-key>",
    "search_api_key": "<tavily-key>",
    "max_retries": 3,
    "score_threshold": 95,
    "timeout": 300
  }'
```

## Dry Run

```bash
curl -X POST http://127.0.0.1:4041/api/run \
  -H 'content-type: application/json' \
  -d '{
    "task": "Automate PR code reviews",
    "provider": "openai",
    "api_key": "<provider-key>",
    "dry_run": true
  }'
```

## MCP Search

```bash
curl 'http://127.0.0.1:4041/api/mcp/search?q=kubernetes'
```
