# Prompt Contracts

The pipeline relies on strict JSON prompt contracts.

## Task Analyzer Contract

Analyzer prompt requires JSON fields:

- `type`, `domain`, `requirements`, `complexity`
- `success_criteria`
- `testable_assertions`

## Recommendation Contract

Recommendation prompt requires JSON fields:

- `llm`, `framework`, `mcp_servers`, `skills`
- `prompt_strategy`, `estimated_tokens`, `estimated_cost`

## Completeness Judge Contract

Scoring prompt expects JSON:

- `score` (0-100)
- `reasoning`

## Parsing Safety

The engine strips markdown fences and parses JSON.
Invalid JSON raises a `ValueError` and fails the stage.
