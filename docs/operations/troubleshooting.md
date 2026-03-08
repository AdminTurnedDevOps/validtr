# Troubleshooting

## Engine Not Reachable

Symptoms:

- CLI errors connecting to `http://127.0.0.1:4041`

Checks:

- engine running with uvicorn
- `engine_addr` config value
- local firewall/network constraints

## Missing API Key

CLI run fails if provider key is missing.

Set one of:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

## Docker Errors

Potential causes:

- Docker daemon not running
- insufficient permissions to Docker socket
- image build failures for base/per-run images

## Empty or Weak Recommendations

Potential causes:

- no `TAVILY_API_KEY` (web search skipped)
- upstream MCP/skills registry fetch failures
- provider JSON formatting failures

## Test Container Failures

Look for:

- malformed generated pytest
- test timeouts
- missing expected output files in `/workspace/output`

Runner output is included in `TestSuiteResult.runner_output`.
