# Docs Versioning Strategy

Current docs are single-version and track `main`.

## Current State

- One live docs site.
- Content reflects latest repository state.
- No version switcher yet.

## Proposed Versioning Model

When `validtr` reaches stable release cadence, move to versioned docs:

1. `latest` (default): tracks active development.
2. `v0.1` (frozen): first tagged release docs.
3. `v0.2+`: additional frozen snapshots per release line.

## Suggested Mechanics

- Keep docs source in repo under `docs/`.
- On release tags, copy release docs snapshot to `docs/versions/vX.Y/`.
- Keep `docs/releases/changelog.md` as release-level summary.

## Versioning Trigger

Introduce versioned docs once:

- CLI and engine APIs are considered stable, and
- breaking doc changes become frequent enough to require snapshots.
