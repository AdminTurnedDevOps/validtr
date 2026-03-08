# Task Lifecycle

This page documents the exact lifecycle implemented in `orchestrator.py`.

## 1. Provider Initialization

The selected provider (`anthropic`, `openai`, `gemini`) is instantiated once and reused by:

- task analyzer
- recommendation reasoning
- test generator
- completeness judge in scoring

## 2. Task Analysis

The analyzer converts raw text into `TaskDefinition` fields:

- `type`
- `domain`
- `requirements` (language/frameworks/capabilities)
- `complexity`
- `success_criteria`
- `testable_assertions`

## 3. Stack Recommendation

Recommendation combines:

- optional Tavily web search results
- MCP server candidates from upstream registries
- skills from upstream GitHub catalogs
- LLM synthesis into a `StackRecommendation`

## 4. Execution Attempt

For each attempt:

- runtime files (`task.json`, `stack.json`) are written
- agent image is selected or built
- container executes and writes artifacts to `/workspace/output`
- artifacts are collected into `ExecutionResult.artifacts`

## 5. Test Generation and Run

- tests are generated from task metadata + artifacts
- tests are written to `/workspace/tests/test_output.py`
- tests run in a separate container with `network_mode=none`

## 6. Scoring

Scoring computes weighted dimensions and pass/fail against threshold.

## 7. Retry

If score is below threshold and retries remain:

- failure dimensions are analyzed
- model upgrade and/or re-search hints are applied
- next attempt runs with adjusted stack

The final response returns the best attempt, not necessarily the last attempt.
