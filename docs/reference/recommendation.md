# Recommendation Engine

The recommendation stage is implemented in `recommender/engine.py` and `recommender/llm_reasoning.py`.

## Inputs

- analyzed task (`TaskDefinition`)
- optional preferred provider
- optional Tavily API key

## Data Sources

- web search via Tavily (`WebSearchProvider`)
- MCP registry data from:
  - official MCP registry (`registry.modelcontextprotocol.io`)
  - Smithery fallback (`registry.smithery.ai`)
- skills catalogs from GitHub:
  - `anthropics/skills`
  - `github/awesome-copilot`

## Parallel Fetch

Recommendation fetches in parallel:

- web results
- relevant MCP servers (filtered)
- full skills catalog

## LLM Output Contract

LLM must return JSON with:

- `llm` provider/model/reason
- `framework`
- `mcp_servers`
- `skills`
- `prompt_strategy`
- `estimated_tokens`
- `estimated_cost`

## Skill Filtering Rules

Returned skills are filtered against the fetched skill catalog.

- unknown skills are dropped
- ambiguous names without `source` are dropped
- canonical output is `"name (source)"`
