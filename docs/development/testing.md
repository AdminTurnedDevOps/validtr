# Test Suite

## Python Engine Tests

Located under `validtr-engine/tests`.

Coverage includes:

- model schemas
- provider factory defaults
- MCP registry parsing/filtering
- provisioning behavior
- scoring and retry logic
- LLM reasoning skill filtering

## Go CLI Tests

Current tests focus on config parsing/validation in:

- `validtr-cli/internal/config/config_test.go`

## Notes

Some runtime behavior (Docker/provider API calls) is integration-heavy and not fully unit-isolated.
