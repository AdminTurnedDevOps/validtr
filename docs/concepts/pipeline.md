# Pipeline

Each `validtr run` executes this sequence:

1. Task analysis
2. Stack recommendation
3. Container provisioning and execution
4. Test generation and test execution
5. Scoring
6. Retry decision

## Retry Behavior

If score is below threshold (default `95`), validtr adjusts stack strategy and retries until:

- score reaches threshold, or
- `max_retries` is reached.
