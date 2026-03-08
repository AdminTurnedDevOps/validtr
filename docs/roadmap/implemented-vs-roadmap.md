# Implemented vs Roadmap

This matrix is based on the current codebase.

| Area | Implemented | Status | Notes |
|---|---|---|---|
| CLI core commands | `run`, `mcp`, `config` | Implemented | In Go/Cobra |
| CLI global config flag | `--config` path override | Implemented | Applies via persistent pre-run |
| Compare providers in one run | `run --compare` | Implemented | Sequential provider runs |
| Dry-run recommendation mode | `run --dry-run` | Implemented | No execution containers |
| Engine API | FastAPI HTTP routes | Implemented | `/api/run`, `/api/mcp/*`, `/api/config/` |
| CLI-engine transport | HTTP/JSON | Implemented | gRPC is not implemented yet |
| Task analysis | LLM JSON classification | Implemented | Produces `TaskDefinition` |
| Stack recommendation | Web + MCP + skills + LLM | Implemented | Fetches MCP/skills at runtime |
| Dockerized execution | Agent container execution | Implemented | Artifacts collected from output dir |
| MCP sidecars | Streamable HTTP compose services | Implemented | Service name `mcp-<name>` |
| Generated tests | LLM-generated pytest | Implemented | Runs in isolated test container |
| Scoring | Weighted code scorer | Implemented | Test/execution/syntax/completeness |
| Retry loop | Score-threshold based retries | Implemented | Model upgrade + re-search hints |
| Dynamic MCP registry integration | Official + Smithery fallback | Implemented | 1-hour in-memory cache |
| Dynamic skills catalogs | GitHub skills catalogs | Implemented | 1-hour in-memory cache |
| UI application | Full local UI | Planned | `validtr-ui` is currently minimal |
| gRPC transport | Typed CLI-engine contracts | Planned | Architecture doc mentions gRPC target |
| Dedicated non-code scorers | Infrastructure/research/automation scorers | Planned | Currently fallback to code scorer |
| History commands | `history` command family | Planned | Mentioned in architecture docs, not in CLI code |
| Stack sharing registry | push/pull/browse community stacks | Planned | Not implemented in current CLI/engine |

## Near-Term Priorities

1. Add dedicated scorers for non-code task types.
2. Stabilize and document API schema as versioned contract.
3. Expand runtime observability (attempt logs/traces surfaced in CLI).
4. Add history and artifact browsing commands.
5. Decide whether to move HTTP to gRPC or keep HTTP and formalize OpenAPI.
