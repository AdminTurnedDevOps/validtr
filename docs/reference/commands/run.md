# `validtr run`

Run task analysis, recommendation, execution, testing, scoring, and retries.

## Usage

```bash
validtr run "Build a FastAPI app with JWT auth"
```

## Flags

- `--provider`: `anthropic`, `openai`, `gemini`
- `--compare`: comma-separated providers
- `--dry-run`: recommendation only
- `--model`: override model id
- `--max-retries`: retry limit
- `--score-threshold`: pass threshold
- `--timeout`: execution timeout seconds

## Modes

## Single provider

```bash
validtr run "Build a CLI in Go" --provider openai
```

## Compare

```bash
validtr run "Build CRUD API" --compare anthropic,openai,gemini
```

Behavior:

- providers run sequentially
- provider with missing API key is skipped

## Dry-run

```bash
validtr run "Automate PR code reviews" --dry-run
```

Behavior:

- no execution or test containers
- returns analyzed task + recommended stack

## Environment

- provider API key must be set for selected provider
- optional `TAVILY_API_KEY` enriches recommendation search
