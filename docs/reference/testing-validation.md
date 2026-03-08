# Testing and Validation

## Generated Output Tests

`TestGenerator` creates pytest code from:

- task description
- success criteria
- testable assertions
- output artifacts

Then executes tests in isolated container:

- image: `validtr-test-runner:latest`
- network: disabled (`network_mode=none`)
- mounts: tests and output as read-only

## Score Dimensions

Current `CodeScorer` weights:

- Test passing: 40
- Execution: 25
- Syntax validity: 15
- Completeness (LLM judge): 20

Composite score determines pass/fail by threshold.

## Completeness Judge

Uses provider JSON response (`score` 0-100).
If judge fails, completeness defaults to 50% of its weight.

## Task-Type Coverage

Only code-generation has dedicated scoring today.
Other task types use code scorer fallback.
