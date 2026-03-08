# Retry Strategy

Retry logic is implemented in `retry/controller.py` and `retry/analysis.py`.

## Retry Decision

Retry only when both are true:

- `score < threshold`
- `attempt_number < max_retries`

## Failure-to-Action Mapping

- low `Test passing`: upgrade model, optionally re-search using failed test messages
- low `Execution`: add MCP server hint + re-search hints
- low `Syntax validity`: upgrade model
- low `Completeness`: upgrade model + re-search

## Model Upgrade Paths

- Anthropic: `claude-sonnet-4-20250514 -> claude-opus-4-20250514`
- OpenAI: `gpt-4o-mini -> gpt-4o -> o3`
- Gemini: `gemini-2.5-flash -> gemini-2.5-pro`

If already at top model for a provider, model remains unchanged.

## Best Attempt Selection

Final response returns the highest score attempt via `max(score)`.
