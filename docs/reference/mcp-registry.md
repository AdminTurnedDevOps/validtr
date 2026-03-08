# MCP Registry Integration

`MCPRegistryClient` fetches server metadata at runtime.

## Registry Order

1. Official MCP registry
2. Smithery fallback

## Cache

- in-memory cache
- TTL: 1 hour

## Search Behavior

`search(query)` tries:

1. official registry search
2. Smithery search
3. local relevance filter on cached dataset

## Relevance Scoring

`get_relevant(query)` scores matches by:

- server name match (higher weight)
- description word match

Results are sorted by score and truncated by `limit`.

## Parsed Fields

Each normalized server includes:

- `name`
- `description`
- `transport`
- `install`
- `credentials`
- `source`
