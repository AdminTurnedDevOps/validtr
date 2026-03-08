# Release and Docs Workflow

## Code + Docs Update Flow

1. Implement feature changes.
2. Update docs pages in `docs/` for the changed behavior.
3. Merge to `main`.
4. GitHub Pages workflow deploys updated docs.

## Docs Deployment Trigger

Workflow file:

- `.github/workflows/docs-gh-pages.yml`

Triggers on:

- push to `main` affecting `docs/**` or workflow file
- manual dispatch

## Recommended Practice

- Keep `docs/releases/changelog.md` updated per release.
- Add roadmap matrix updates when implementation status changes.
