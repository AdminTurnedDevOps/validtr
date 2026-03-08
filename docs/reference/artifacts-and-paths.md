# Artifacts and Paths

## Engine Runtime Directory

Per-run files are created under temp storage by default:

```text
/tmp/validtr-runs/<run_id>
```

## Key Files

- `docker-compose.yml`
- `Dockerfile.agent`
- `entrypoint.py`
- `agent_loop.py`
- `workspace/task.json`
- `workspace/stack.json`
- `workspace/output/*` (generated artifacts)
- `workspace/tests/test_output.py` (generated tests)

## Artifact Collection

Execution stage reads all files under `workspace/output` and returns them as:

- `artifacts: { "relative/path": "content" }`

Binary/unreadable files are represented as:

- `"<binary file>"`
