# CLI Reference

This page is the entrypoint for all CLI command documentation.

## Available Commands

- `completion`
- `config`
- `help`
- `mcp`
- `run`

## Start Here

- command index: [/reference/commands/index](/reference/commands/index)
- run command: [/reference/commands/run](/reference/commands/run)
- mcp command: [/reference/commands/mcp](/reference/commands/mcp)
- config command: [/reference/commands/config](/reference/commands/config)
- completion command: [/reference/commands/completion](/reference/commands/completion)
- help command: [/reference/commands/help](/reference/commands/help)

## Command Behavior Notes

- `run --dry-run` calls engine with `dry_run=true` and does not execute Docker workloads.
- `run --compare` runs each provider sequentially and skips providers with missing API keys.
- `run` and `run --compare` pass `TAVILY_API_KEY` to engine as `search_api_key` when present.
- CLI config values are used only if corresponding flags are not explicitly set.

## Global Flags

- `-c, --config`: override config path (default `~/.validtr/config.yaml`)

## Exit Behavior

The root command exits with code `1` on command error.
