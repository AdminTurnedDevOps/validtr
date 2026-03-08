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

## API Endpoints Summary

- `GET /health`
- `GET /api/config/`
- `GET /api/mcp/servers`
- `GET /api/mcp/search?q=...`
- `GET /api/mcp/servers/{name}`
- `POST /api/run`

## `POST /api/run` Error Mapping

- `400`: invalid provider or other validation errors
- `401`: authentication-like provider errors
- `429`: rate limit or permission-like provider errors

## Dry Run Response

When `dry_run=true`, response is:

- `task`: analyzed `TaskDefinition`
- `recommendation`: full `StackRecommendation`

## Related

- examples: [/reference/api-examples](/reference/api-examples)
- errors: [/reference/error-catalog](/reference/error-catalog)
