# Current Limitations

This page reflects current implementation status.

## Implemented

- CLI with `run`, `mcp`, `config`
- engine REST API
- provider adapters (Anthropic/OpenAI/Gemini)
- Docker-based execution
- generated pytest validation
- weighted scoring and retry loop
- runtime MCP and skills discovery

## Not Yet Implemented

- gRPC transport between CLI and engine (HTTP used today)
- fully implemented UI experience (`validtr-ui` is currently minimal)
- dedicated scorers for infrastructure/research/automation
- persistent run history commands in CLI
- hosted community stack registry

## Practical Constraints

- depends on external APIs (provider, registries, optional Tavily)
- registry data can vary over time
- generated tests and completeness scoring depend on LLM quality
