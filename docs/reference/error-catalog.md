# Error Catalog

## CLI Errors

## Missing provider key

Cause:

- selected provider env var is not set

Shape:

- `no API key found for provider ...`

## Engine request failure

Cause:

- engine process down
- bad `engine_addr`

Shape:

- `engine request failed: ...`

## API Errors (`POST /api/run`)

- `400`: invalid provider or malformed request
- `401`: authentication failures from provider SDK
- `429`: rate limit/permission-style failures
- `500`: unhandled engine/runtime failure

## Runtime Errors

- Docker unavailable
- image build failure
- container timeout
- invalid LLM JSON output for analyzer/recommendation/scoring judge
