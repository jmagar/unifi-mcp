# CI/CD Workflows

GitHub Actions configuration for unifi-mcp.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main/feature branches, PRs | Lint, typecheck, test, security |
| `docker-publish.yml` | Push to main, tags, PRs | Build and push Docker image |
| `publish-pypi.yml` | Version tags (`v*.*.*`) | Publish to PyPI and MCP Registry |

## CI Workflow (`ci.yml`)

### Jobs

| Job | Runner | Steps |
|-----|--------|-------|
| `lint` | ubuntu-latest | ruff check, ruff format --check |
| `typecheck` | ubuntu-latest | ty check unifi_mcp/ |
| `test` | ubuntu-latest | pytest (excludes slow, integration) |
| `version-sync` | ubuntu-latest | Verify version across pyproject.toml, plugin.json, .app.json |
| `contract-drift` | ubuntu-latest | scripts/lint-plugin.sh |
| `docker-security` | ubuntu-latest | Dockerfile security, no baked env, ignore files |
| `mcp-integration` | ubuntu-latest | Live tests (requires secrets, runs after lint+typecheck+test) |

### Version Sync Check

Ensures these files all have the same version:
- `pyproject.toml` (`[project].version`)
- `.claude-plugin/plugin.json` (`version`)
- `.codex-plugin/plugin.json` (`version`)
- `.app.json` (`version`)

### Branch Triggers

Push: `main`, `chore/**`, `feat/**`, `fix/**`
PRs: `main`

## Docker Publish (`docker-publish.yml`)

Builds multi-platform Docker images (`linux/amd64`, `linux/arm64`) and pushes to GitHub Container Registry.

### Tags Generated

| Event | Tags |
|-------|------|
| Push to main | `latest`, `main`, `sha-<commit>` |
| Version tag | `v1.0.1`, `1.0`, `1`, `sha-<commit>` |
| PR | `pr-<number>` (build only, no push) |

### Security Scanning

After push, runs Trivy vulnerability scan on `CRITICAL` and `HIGH` severity.

## PyPI Publish (`publish-pypi.yml`)

Triggered by version tags (`v*.*.*`).

### Steps

1. Verify tag matches `pyproject.toml` version
2. Build package with `uv build`
3. Publish to PyPI with attestations
4. Create GitHub Release with release notes
5. Publish to MCP Registry (`tv.tootie/unifi-mcp`) via DNS auth on `tootie.tv`

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Release creation, package publish |
| `MCP_PRIVATE_KEY` | MCP Registry DNS authentication |

## Release Process

```bash
# Via Justfile (recommended)
just publish patch   # Bump patch version
just publish minor   # Bump minor version
just publish major   # Bump major version
```

The `publish` recipe:
1. Verifies on `main` branch with clean working tree
2. Bumps version in pyproject.toml, plugin.json files, gemini-extension.json
3. Commits, tags, and pushes
4. CI/CD workflows handle the rest

## See Also

- [TESTS.md](TESTS.md) — Testing details
- [PUBLISH.md](PUBLISH.md) — Publishing strategy
- [DEV.md](DEV.md) — Development workflow
