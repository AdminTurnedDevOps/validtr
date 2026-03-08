# Data Models

Core schemas are under `validtr-engine/models`.

## Task Models

- `TaskType`: `code-generation`, `infrastructure`, `research`, `automation`
- `Complexity`: `simple`, `moderate`, `complex`
- `TaskRequirements`: language/frameworks/capabilities
- `TaskDefinition`: normalized task payload

## Stack Models

- `LLMRecommendation`
- `FrameworkRecommendation`
- `MCPServerRecommendation`
- `StackRecommendation`
- `MCPTransport`: `stdio` or `streamable-http`

## Execution Models

- `ExecutionResult`: run success, artifacts, output dir, error
- `ExecutionTrace`: llm/tool call log and totals
- `LLMCall`, `ToolCall`

## Test Models

- `TestStatus`: passed/failed/error/skipped
- `SingleTestResult`
- `TestSuiteResult` with computed `pass_rate`

## Scoring Models

- `DimensionScore`
- `ScoreResult` with threshold check
- `AttemptResult`
- `FinalResult`
- `StackSummary`
