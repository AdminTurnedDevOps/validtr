# Engine API

Default engine address:

```text
http://127.0.0.1:4041
```

## Health

- `GET /health`

## Run

- `POST /api/run`

Request fields:

- `task` string
- `provider` string
- `model` string optional
- `api_key` string optional
- `search_api_key` string optional
- `max_retries` int
- `score_threshold` float
- `timeout` int
- `dry_run` bool

## MCP

- `GET /api/mcp/servers`
- `GET /api/mcp/search?q=...`
- `GET /api/mcp/servers/{name}`
