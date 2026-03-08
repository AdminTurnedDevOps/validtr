# `validtr config`

Manage local non-secret configuration.

## Subcommands

- `validtr config set <key> <value>`
- `validtr config show`

## Supported Keys

- `provider`
- `score-threshold`
- `max-retries`
- `timeout`
- `engine-addr`

## Examples

```bash
validtr config set provider anthropic
validtr config set score-threshold 90
validtr config set max-retries 5
validtr config set timeout 600
validtr config set engine-addr http://127.0.0.1:4041
validtr config show
```

## Security

API keys are not written to config file.
Use environment variables only.
