# validtr — Architecture Design Document (v3 — Final)

## Overview

validtr is a CLI tool (Go/Cobra) backed by a Python engine that takes a natural language task description, recommends the optimal agentic stack (LLM, agent framework, MCP servers, agent skills), provisions that stack in containers, executes the task end-to-end, generates tests, and scores the result. If the score falls below 95%, it iterates — adjusting the stack and retrying until the threshold is met or max retries are exhausted.

Users can compare the same task across multiple LLM providers in a single run. Results can be viewed in the CLI or through an optional web UI (TypeScript/React) served locally. Community stack sharing is built in from day one.

---

## Core Principles

- **Local-first**: Everything runs on the user's machine. CLI, engine, UI, containers — all local.
- **Container-isolated**: Every test run is a clean, reproducible environment.
- **Framework-agnostic**: Can recommend and provision any agent framework.
- **Provider-flexible**: Supports Anthropic, OpenAI, and Google Gemini.
- **Empirical, not theoretical**: The tool doesn't just suggest — it proves.
- **Tests are mandatory**: No validation without generated tests. Tests are the proof.
- **Always online**: Web search and LLM reasoning are core to the recommendation engine. No offline mode.
- **Always recommend the best**: Even if the user has existing tools, validtr recommends the optimal stack regardless.
- **CLI-primary, UI-optional**: Full functionality via CLI. UI adds visualization and community features, served locally.

---

## Architecture Decisions (Locked)

| Decision | Choice | Rationale |
|---|---|---|
| Product name | **validtr** | Short, memorable, implies validation |
| CLI language | **Go (Cobra)** | Single binary, zero runtime deps for user |
| Engine language | **Python** | AI/agent SDK ecosystem compatibility |
| CLI ↔ Engine | **gRPC** | Typed contracts, streaming for real-time output |
| UI framework | **React + TypeScript** | Bundled into Go binary, served locally |
| UI hosting | **Local only (localhost:4040)** | No hosted UI initially. Future: hosted option |
| Community registry | **Local-first** | Registry data stored locally, future: hosted sync |
| Test generation | **Mandatory** | Tests are always generated. No validation without tests |
| Offline mode | **Not supported** | Web search + LLM are core. Offline defeats the purpose |
| Existing tool detection | **Ignored** | Always recommends the best stack regardless of what exists locally |
| Containers | **Docker + Docker Compose** | Isolation, reproducibility, clean teardown |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Machine                           │
│                                                                 │
│  ┌──────────────┐       ┌──────────────────────────────────┐    │
│  │  Go CLI      │       │  Python Engine                   │    │
│  │  (Cobra)     │◄─────►│  (FastAPI @ localhost:4041)      │    │
│  │              │ gRPC  │                                  │    │
│  │  • UX/Output │       │  • Task Analyzer                │    │
│  │  • Config    │       │  • Recommendation Engine         │    │
│  │  • Auth      │       │  • Stack Provisioner             │    │
│  │  • History   │       │  • Execution Engine              │    │
│  │              │       │  • Test Generator                │    │
│  └──────────────┘       │  • Scoring Engine                │    │
│                         │  • Retry Controller              │    │
│  ┌──────────────┐       │  • Comparison Engine             │    │
│  │  Web UI      │       │  • Community Manager             │    │
│  │  (React/TS)  │──────►│                                  │    │
│  │  :4040       │ HTTP/ └──────────┬───────────────────────┘    │
│  │  local only  │ SSE              │                            │
│  └──────────────┘       ┌──────────▼───────────────────────┐    │
│                         │  Docker Environment              │    │
│                         │  (per test run)                   │    │
│                         │                                  │    │
│                         │  • Agent container(s)            │    │
│                         │  • MCP server containers         │    │
│                         │  • Test runner container          │    │
│                         │  • kind cluster (if K8s tasks)   │    │
│                         └──────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                    External API Calls
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ LLM APIs │   │ Web      │   │ MCP          │
        │ Anthropic│   │ Search   │   │ Registries   │
        │ OpenAI   │   │ Tavily/  │   │ mcp.so       │
        │ Gemini   │   │ Brave    │   │ Smithery     │
        └──────────┘   └──────────┘   └──────────────┘
```

---

## Go CLI (Cobra)

Single binary distribution. Zero runtime dependencies for the end user (aside from Docker).

### Commands

```bash
# ══════════════════════════════════════════════
# Core — run tasks
# ══════════════════════════════════════════════

# Run a task with a single provider
validtr run "I want to build a FastAPI web app with JWT auth" \
  --provider anthropic

# Run and compare across multiple providers
validtr run "I want to troubleshoot K8s pod failures" \
  --compare anthropic,openai,gemini

# Dry run — recommend a stack but don't execute
validtr run "Automate PR code reviews" --dry-run

# Run from a task file
validtr run --task-file task.yaml

# Override defaults
validtr run "Build a CLI in Go" \
  --provider openai \
  --model gpt-4o \
  --max-retries 5 \
  --score-threshold 90 \
  --timeout 600

# ══════════════════════════════════════════════
# MCP server discovery
# ══════════════════════════════════════════════

validtr mcp list
validtr mcp search "kubernetes"
validtr mcp info filesystem

# ══════════════════════════════════════════════
# History and results
# ══════════════════════════════════════════════

validtr history
validtr history show <run-id>
validtr history export <run-id> --format json

# ══════════════════════════════════════════════
# Community stack sharing
# ══════════════════════════════════════════════

validtr stack push <run-id>
validtr stack browse --task-type code-generation --sort score
validtr stack pull <stack-id> --run
validtr stack export --all --output stacks.json
validtr stack import stacks.json

# ══════════════════════════════════════════════
# UI (local)
# ══════════════════════════════════════════════

validtr ui
validtr ui --open

# ══════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════

validtr config set provider anthropic
validtr config set api-key anthropic sk-ant-...
validtr config set mcp-credential github-pat ghp_...
validtr config show

# ══════════════════════════════════════════════
# Engine management
# ══════════════════════════════════════════════

validtr engine status
validtr engine update
```

### CLI Output (Single Run)

```
╭──────────────────────────────────────────────────╮
│  validtr — Run #a3f7c2                           │
│  Task: "Build a FastAPI web app with JWT auth"   │
├──────────────────────────────────────────────────┤
│                                                  │
│  ▸ Analyzing task...              ✓ complete     │
│  ▸ Searching MCP registries...    ✓ 12 servers   │
│  ▸ Web search...                  ✓ 8 results    │
│  ▸ Generating recommendation...   ✓ complete     │
│                                                  │
│  Recommended Stack:                              │
│  ┌───────────┬──────────────────────────────┐    │
│  │ LLM       │ Claude Sonnet 4              │    │
│  │ Framework │ None (direct tool calling)    │    │
│  │ MCP       │ filesystem, github            │    │
│  │ Skills    │ code-gen, dep-management      │    │
│  └───────────┴──────────────────────────────┘    │
│                                                  │
│  ▸ Provisioning containers...     ✓ 2 containers │
│  ▸ Executing task...              ✓ 47s          │
│  ▸ Generating tests...            ✓ 12 tests     │
│  ▸ Running tests...               ✓ 11/12 passed │
│  ▸ Scoring output...              ✓ complete     │
│                                                  │
│  Score: 97/100                    ✅ PASS         │
│  ┌────────────────────┬───────┐                  │
│  │ Test passing       │ 37/40 │                  │
│  │ Execution          │ 25/25 │                  │
│  │ Syntax validity    │ 15/15 │                  │
│  │ Completeness       │ 20/20 │                  │
│  └────────────────────┴───────┘                  │
│                                                  │
│  Artifacts: ./validtr-output/a3f7c2/             │
│  Tests:     ./validtr-output/a3f7c2/tests/       │
│  Cost: $0.04 (16,400 tokens)                     │
│  Time: 1m 22s                                    │
│                                                  │
│  View in UI: validtr ui --run a3f7c2             │
╰──────────────────────────────────────────────────╯
```

### CLI Output (Comparison)

```
╭────────────────────────────────────────────────────────────────╮
│  validtr — Comparison Report                                   │
│  Task: "Build a REST API with CRUD endpoints"                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│                  Anthropic      OpenAI        Gemini            │
│  Model           Sonnet 4       GPT-4o        2.5 Flash        │
│  ─────────────────────────────────────────────────────         │
│  Overall Score   97/100 ✅      91/100 ⚠️     88/100 ⚠️       │
│  ─────────────────────────────────────────────────────         │
│  Test passing    37/40          32/40         29/40            │
│  Execution       25/25          23/25         22/25            │
│  Syntax          15/15          15/15         15/15            │
│  Completeness    20/20          21/25         22/25            │
│  ─────────────────────────────────────────────────────         │
│  Tests Gen'd     12             10            11               │
│  Tests Passed    11/12          8/10          7/11             │
│  ─────────────────────────────────────────────────────         │
│  Tokens          16,400         21,100        13,800           │
│  Cost            $0.04          $0.06         $0.02            │
│  Time            1m 22s         1m 48s        58s              │
│  Retries         0              1             1                │
│                                                                │
│  🏆 Winner: Anthropic (Claude Sonnet 4) — highest score        │
│  💰 Best value: Gemini (2.5 Flash) — lowest cost               │
│  ⚡ Fastest: Gemini (2.5 Flash) — 58s                          │
│                                                                │
│  View details: validtr ui --run a3f7c2                         │
╰────────────────────────────────────────────────────────────────╯
```

---

## Core Pipeline

### Step 1: Task Analyzer

**Input:** "I want to build a FastAPI web app with JWT auth"

**Output:**
```yaml
task:
  id: "a3f7c2"
  raw_input: "I want to build a FastAPI web app with JWT auth"
  type: code-generation
  domain: web
  requirements:
    language: python
    frameworks: [fastapi]
    capabilities: [jwt-authentication, api-endpoints, database]
  complexity: moderate
  success_criteria:
    - "Produces runnable FastAPI application"
    - "Includes JWT authentication middleware"
    - "Has at least one protected endpoint"
    - "Includes requirements.txt or pyproject.toml"
    - "Application starts without errors"
  testable_assertions:
    - "Server starts on a configurable port"
    - "Unauthenticated request to protected endpoint returns 401"
    - "Valid JWT token grants access to protected endpoint"
    - "Invalid JWT token is rejected"
    - "Token generation endpoint returns valid JWT"
```

The `testable_assertions` field is critical — it becomes the basis for mandatory test generation in Step 5.

---

### Step 2: Recommendation Engine

Three sources run in parallel:

**2a. Web Search** — current best practices, benchmarks, compatibility info.

**2b. MCP Registry Lookup** — queries mcp.so, Smithery, GitHub for available servers. Captures transport type, credentials, capabilities, install method.

**2c. LLM Reasoning** — synthesizes everything into a concrete stack recommendation.

**Key rule:** Always recommends the best stack for the task, regardless of what the user has installed locally.

**Output:**
```yaml
recommendation:
  llm:
    provider: anthropic
    model: claude-sonnet-4-20250514
    reason: "Strong code generation, native tool calling, structured output"
  framework:
    name: null
    reason: "Single-task code generation — no orchestration needed"
  mcp_servers:
    - name: filesystem
      transport: stdio
      install: "npx -y @modelcontextprotocol/server-filesystem"
      credentials: none
  skills:
    - "code-generation"
    - "dependency-management"
    - "test-generation"  # Always included
  estimated_tokens: 16400
  estimated_cost: "$0.04"
```

---

### Step 3: Stack Provisioner

Generates a Docker Compose environment from the StackRecommendation.

```
┌────────────────────────────────────────────────┐
│  Docker Compose Environment (per run)          │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │  Agent Container                         │  │
│  │  • Python 3.12 + Node.js                 │  │
│  │  • Framework (if recommended)            │  │
│  │  • stdio MCP servers (child processes)   │  │
│  │  • LLM provider SDK                      │  │
│  │  • Credentials (env vars, runtime only)  │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │  Test Runner Container                   │  │
│  │  • pytest / language-appropriate runner   │  │
│  │  • Access to agent output artifacts      │  │
│  │  • Isolated from agent (can't cheat)     │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │  MCP Server Containers (if needed)       │  │
│  │  (streamable-http servers only)          │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │  kind Cluster (K8s tasks only)           │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

Credentials are injected as runtime environment variables from `~/.validtr/config.yaml`. The CLI checks all required credentials before provisioning and prompts for any that are missing.

---

### Step 4: Execution Engine

1. Inject task description + success criteria into agent's system prompt
2. Start agent loop
3. Agent uses MCP servers and skills to produce output
4. Capture: full traces, tool calls, LLM calls, artifacts, timing, tokens

**Safety limits (configurable):**
- Timeout: 5 min
- Max LLM calls: 50
- Max MCP tool calls: 100

---

### Step 5: Test Generator (MANDATORY)

No validation occurs without tests. After execution produces output, the test generator creates tests to verify it.

```
Execution output artifacts
        +
TaskDefinition.testable_assertions
        +
TaskDefinition.success_criteria
        │
        ▼
LLM generates tests
(separate call — never sees agent reasoning,
 only task description + success criteria +
 testable assertions + output artifacts)
        │
        ▼
Tests written to /workspace/tests/
        │
        ▼
Test runner executes in ISOLATED container
(only has access to output artifacts, not agent internals)
        │
        ▼
Results: X/Y passed, failure details per test
```

**Test generation by task type:**

**Code tasks:** Unit tests, integration tests, smoke tests (app starts?), assertion tests from `testable_assertions`.

**Infrastructure tasks:** Manifest validation, dry-run against kind, state verification post-apply, safety scans for destructive operations.

**Research tasks:** Source verification (URLs return 200?), completeness checks, consistency cross-referencing, structure validation.

**Automation tasks:** Workflow completion, output shape validation, idempotency, error path handling.

**Test isolation is critical.** Tests run in a separate container. The test runner only sees output artifacts — not the agent's conversation, reasoning, or intermediate steps. This prevents gaming the score.

**Each retry generates fresh tests.** Since a stack change may produce structurally different output, tests must be regenerated per attempt.

---

### Step 6: Scoring Engine

Composite score (0-100) from test results + quality signals.

**Tests are the largest weight in every task type:**

| Task Type | Test Passing | Execution | Syntax/Validity | Completeness |
|---|---|---|---|---|
| Code | 40% | 25% | 15% | 20% |
| Infrastructure | 40% | — | 20% safety, 20% validity | 20% |
| Research | 30% + 40% LLM judge | — | 15% source quality | 15% coherence |
| Automation | 40% | 25% | — | 20% correctness, 15% efficiency |

**95% threshold.** Below 95 means a meaningful quality issue that a different stack might fix. Above 95 means production-quality output with acceptable non-deterministic variance.

---

### Step 7: Retry Controller

```
Score < 95%
    │
    ▼
Analyze which tests failed + weakest scoring dimensions
    │
    ▼
Map to targeted adjustment:
    ├── Code quality failures → stronger model
    ├── Missing feature failures → add MCP server or skill
    ├── Execution failures → check deps, try different framework
    ├── Safety failures → safety-focused prompt adjustments
    ├── LLM judge low → model with better reasoning
    │
    ▼
Adjusted StackRecommendation (not from scratch)
    │
    ▼
Re-provision → Re-execute → Fresh tests → Re-score
    │
    ▼
All attempts tracked. After max retries (default 3),
return best-scoring result + comparison of all attempts.
```

---

## Multi-Provider Comparison

```
validtr run "Build a REST API" --compare anthropic,openai,gemini

Task Analyzer (once, shared)
        │
        ▼
┌───────┼───────┐
▼       ▼       ▼
Anthropic OpenAI Gemini     ← Each gets isolated Docker env
│       │       │           ← All run in PARALLEL
▼       ▼       ▼
Score   Score   Score
│       │       │
└───────┼───────┘
        ▼
Comparison Report (ranked by score, cost, speed)
```

---

## Community Stack Registry (Local-First)

### Local Storage

```
~/.validtr/
├── config.yaml
├── history/
│   └── *.json              # Run history
└── stacks/
    ├── registry.db          # SQLite index
    └── data/
        └── *.json           # Stack records
```

### Future: Hosted Sync

The `export` / `import` commands provide the bridge:

```bash
validtr stack export --all --output stacks.json   # Share manually
validtr stack import stacks.json                   # Import from others
```

When a hosted registry is added later, `push` and `browse` will sync to both local and remote. The local-first design means the tool never depends on a hosted service to function.

---

## Web UI (Local, React/TypeScript)

Bundled into Go binary via `go:embed`. Served on `localhost:4040`.

### Pages

1. **Dashboard** — recent runs, quick-run input, provider summaries
2. **Run Detail** — task analysis, recommendation reasoning, execution trace, test results panel (pass/fail with details), score breakdown, artifact viewer, cost breakdown
3. **Comparison View** — side-by-side providers, radar charts, cost vs quality scatter, test pass rates, artifact diffs
4. **Community Stacks** — browse/search local registry, filter by type/domain/provider/score, one-click re-run
5. **MCP Explorer** — browse registries, filter by transport/credentials/capability

### Stack

- React 19 + TypeScript
- Tailwind CSS
- Recharts
- Zustand
- Vite (output bundled into Go binary)

---

## Project Structure

### Go CLI — `validtr-cli/`

```
cmd/
├── root.go
├── run.go
├── mcp.go
├── history.go
├── stack.go
├── ui.go
├── config.go
└── engine.go
internal/
├── engine/
│   ├── manager.go          # Python engine lifecycle
│   └── client.go           # gRPC client
├── config/
│   ├── config.go
│   └── credentials.go
├── output/
│   ├── renderer.go         # lipgloss
│   ├── progress.go
│   ├── table.go
│   └── color.go
├── ui/
│   ├── server.go           # Embedded HTTP server
│   └── assets/             # go:embed React build
└── proto/
    └── validtr.proto
main.go
go.mod
```

### Python Engine — `validtr-engine/`

```
api/
├── server.py
├── routes/
│   ├── run.py
│   ├── compare.py
│   ├── history.py
│   ├── mcp.py
│   ├── stack.py
│   └── config.py
└── streaming.py

analyzer/
├── task_analyzer.py
└── prompts.py

recommender/
├── engine.py
├── web_search.py
├── mcp_registry.py
├── llm_reasoning.py
└── prompts.py

provisioner/
├── compose_generator.py
├── image_builder.py
├── credentials.py
└── templates/
    ├── agent.Dockerfile
    ├── test-runner.Dockerfile
    └── mcp-server.Dockerfile

executor/
├── engine.py
├── trace.py
└── safety.py

test_generator/
├── engine.py
├── code_tests.py
├── infra_tests.py
├── research_tests.py
├── automation_tests.py
├── runner.py
└── prompts.py

scorer/
├── engine.py
├── code_scorer.py
├── infra_scorer.py
├── research_scorer.py
├── automation_scorer.py
└── prompts.py

comparison/
├── engine.py
└── report.py

retry/
├── controller.py
└── analysis.py

community/
├── registry.py
├── push.py
└── pull.py

providers/
├── base.py
├── anthropic.py
├── openai.py
└── gemini.py

models/
├── task.py
├── stack.py
├── result.py
├── test_result.py
├── score.py
└── comparison.py

utils/
├── docker.py
├── search.py
├── tokens.py
└── cache.py
```

### Web UI — `validtr-ui/`

```
src/
├── App.tsx
├── main.tsx
├── api/
│   ├── client.ts
│   └── types.ts
├── pages/
│   ├── Dashboard.tsx
│   ├── RunDetail.tsx
│   ├── Comparison.tsx
│   ├── Community.tsx
│   └── MCPExplorer.tsx
├── components/
│   ├── ScoreGauge.tsx
│   ├── ScoreBreakdown.tsx
│   ├── TestResults.tsx
│   ├── StackCard.tsx
│   ├── TraceViewer.tsx
│   ├── ArtifactViewer.tsx
│   ├── ComparisonTable.tsx
│   ├── RadarChart.tsx
│   ├── CostChart.tsx
│   ├── RunProgress.tsx
│   └── MCPServerCard.tsx
├── hooks/
│   ├── useRun.ts
│   ├── useStream.ts
│   └── useCommunity.ts
└── styles/
    └── globals.css
package.json
tsconfig.json
vite.config.ts
tailwind.config.ts
```

---

## Technology Summary

| Component | Technology | Rationale |
|---|---|---|
| CLI | Go + Cobra + lipgloss | Single binary, rich TUI |
| Engine | Python + FastAPI | AI SDK ecosystem |
| CLI ↔ Engine | gRPC | Typed, streaming |
| UI | React + TypeScript + Tailwind | Bundled into Go binary |
| UI ↔ Engine | HTTP + SSE | Real-time updates |
| Containers | Docker + Docker Compose | Isolation |
| Web Search | Tavily or Brave Search API | Programmatic search |
| MCP Registries | mcp.so, Smithery, GitHub API | Dynamic discovery |
| LLM Providers | Anthropic, OpenAI, Google GenAI SDKs | Direct integration |
| Test Runner | pytest + language-appropriate runners | Standard, extensible |
| Local K8s | kind | K8s-in-Docker for infra tasks |
| Local Storage | SQLite + JSON | No external DB |
| Config | YAML (~/.validtr/config.yaml) | Human-readable |

---

## Prerequisites for Users

- **Docker** (required — containers are the execution environment)
- **Python 3.12+** (for the engine)
- **At least one LLM provider API key** (Anthropic, OpenAI, or Gemini)

---

## Build Order (Suggested)

### Phase 1: Core Loop
1. Task Analyzer
2. Recommendation Engine (web search + MCP registry + LLM)
3. Stack Provisioner (Docker Compose generation)
4. Execution Engine
5. Test Generator
6. Scoring Engine
7. Basic CLI (`validtr run` with single provider)

### Phase 2: Iteration and Comparison
8. Retry Controller
9. Multi-provider comparison (`--compare`)
10. History tracking (`validtr history`)

### Phase 3: Community and UI
11. Community stack registry (local SQLite)
12. `validtr stack push/browse/pull`
13. Web UI (React/TypeScript)
14. `validtr ui`

### Phase 4: Polish
15. MCP Explorer (`validtr mcp list/search/info`)
16. Config management (`validtr config`)
17. Export/import for future hosted sync
18. Binary distribution (GitHub Releases, Homebrew)\