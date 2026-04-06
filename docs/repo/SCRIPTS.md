# Scripts Reference

Scripts used for maintenance, hooks, and testing.

## Maintenance Scripts (`scripts/`)

| Script | Purpose | CI Job |
|--------|---------|--------|




| `smoke-test.sh` | End-to-end smoke test against running server | manual |

## Hook Scripts (`bin/`)

| Script | Trigger | Purpose |
|--------|---------|---------|
The `sync-uv.sh` hook keeps the repository lockfile and persistent Python environment in sync at session start.


## Test Scripts

| Script | Purpose |
|--------|---------|
| `tests/test_live.sh` | Live integration tests against a running server with real UniFi controller |

## Running Scripts

Directly

```bash

bash bin/smoke-test.sh
```

Via Justfile

```bash
just check-contract      # no-op placeholder
just validate-skills     # no-op placeholder
just test-live           # Health check against running server
```

In CI

All maintenance scripts run in the CI pipeline:

- `tests/test_live.sh` in the `mcp-integration` job

## See Also

- [RECIPES.md](RECIPES.md) — Justfile recipes
- [CICD](../mcp/CICD.md) — CI workflow details
