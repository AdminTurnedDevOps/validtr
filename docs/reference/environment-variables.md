# Environment Variables

## Provider Keys

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

## Recommendation Search

- `TAVILY_API_KEY`

## MCP Credentials

Some MCP servers require additional env vars. These are surfaced by MCP metadata and may include values like:

- `DATABASE_URL`
- `GITHUB_TOKEN`
- `AWS_ACCESS_KEY_ID`
- `KUBECONFIG`

Credential names come from registry server definitions and can vary over time.

## Runtime-Injected Vars (containers)

- `VALIDTR_RUN_ID`
- `VALIDTR_PROVIDER`
- `VALIDTR_MODEL`
