# `validtr mcp`

MCP server discovery and lookup.

## Subcommands

- `validtr mcp list`
- `validtr mcp search <query>`
- `validtr mcp info <name>`

## `mcp list`

Prints table:

- `NAME`
- `TRANSPORT`
- `DESCRIPTION`

## `mcp search`

Searches upstream registry data and prints install hints.

```bash
validtr mcp search kubernetes
```

## `mcp info`

Shows full details for one server.

```bash
validtr mcp info filesystem
```

Output fields:

- name
- transport
- description
- install
- credentials
