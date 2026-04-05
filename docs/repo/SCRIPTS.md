# Scripts Reference

Scripts used for maintenance, hooks, and testing.

## Maintenance Scripts (`scripts/`)

| Script | Purpose | CI Job |
|--------|---------|--------|
| `lint-plugin.sh` | Validate skill/tool contract drift; ensures SKILL.md matches registered tools | `contract-drift` |
| `check-docker-security.sh` | Audit Dockerfile: non-root user, no COPY .env, no ARG secrets | `docker-security` |
| `check-no-baked-env.sh` | Detect environment variables baked into Docker images | `docker-security` |
| `ensure-ignore-files.sh` | Verify .gitignore and .dockerignore contain required patterns | `docker-security` |
| `check-outdated-deps.sh` | Check for outdated Python dependencies | manual |
| `smoke-test.sh` | End-to-end smoke test against running server | manual |

## Hook Scripts (`hooks/scripts/`)

| Script | Trigger | Purpose |
|--------|---------|---------|
| `sync-env.sh` | SessionStart | Copy userConfig values to `.env` |
| `fix-env-perms.sh` | PostToolUse (Write/Edit/Bash) | Enforce `chmod 600` on `.env` |
| `ensure-ignore-files.sh` | SessionStart, PostToolUse | Verify ignore file entries |

## Test Scripts

| Script | Purpose |
|--------|---------|
| `tests/test_live.sh` | Live integration tests against a running server with real UniFi controller |

## Running Scripts

### Directly

```bash
bash scripts/lint-plugin.sh
bash scripts/check-docker-security.sh Dockerfile
bash scripts/smoke-test.sh
```

### Via Justfile

```bash
just check-contract      # lint-plugin.sh
just validate-skills     # lint-plugin.sh
just test-live           # Health check against running server
```

### In CI

All maintenance scripts run in the CI pipeline:
- `lint-plugin.sh` in the `contract-drift` job
- `check-docker-security.sh`, `check-no-baked-env.sh`, `ensure-ignore-files.sh` in the `docker-security` job
- `tests/test_live.sh` in the `mcp-integration` job

## See Also

- [RECIPES.md](RECIPES.md) — Justfile recipes
- [CICD](../mcp/CICD.md) — CI workflow details
