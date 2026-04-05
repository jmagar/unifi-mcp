# Publishing Strategy

Versioning and release workflow for unifi-mcp.

## Versioning

Semantic versioning (MAJOR.MINOR.PATCH). All version-bearing files must be in sync:

| File | Field |
|------|-------|
| `pyproject.toml` | `[project].version` |
| `.claude-plugin/plugin.json` | `version` |
| `.codex-plugin/plugin.json` | `version` |
| `gemini-extension.json` | `version` |
| `.app.json` | `version` |
| `server.json` | `version` and `packages[0].version` |

## Release Process

### Via Justfile (Recommended)

```bash
just publish patch   # 1.0.1 -> 1.0.2
just publish minor   # 1.0.1 -> 1.1.0
just publish major   # 1.0.1 -> 2.0.0
```

This recipe:
1. Verifies you are on `main` with a clean working tree
2. Bumps version in pyproject.toml and all JSON manifests
3. Commits with message `release: vX.Y.Z`
4. Creates git tag `vX.Y.Z`
5. Pushes to origin with tags

### Automated Workflows

After the tag push, CI handles:

1. **Docker**: `docker-publish.yml` builds and pushes to `ghcr.io/jmagar/unifi-mcp`
2. **PyPI**: `publish-pypi.yml` builds, publishes to PyPI, creates GitHub Release
3. **MCP Registry**: `publish-pypi.yml` publishes to `tv.tootie/unifi-mcp` via DNS auth

## Distribution Channels

| Channel | Package Name | Format |
|---------|-------------|--------|
| PyPI | `mcp-unifi` | Python wheel |
| GitHub Container Registry | `ghcr.io/jmagar/unifi-mcp` | Docker image (amd64, arm64) |
| MCP Registry | `tv.tootie/unifi-mcp` | Registry entry |
| GitHub Releases | `jmagar/unifi-mcp` | Source + wheel artifacts |

## MCP Registry

Published using `mcp-publisher` with DNS authentication on `tootie.tv`.

Registry schema (`server.json`):

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "tv.tootie/unifi-mcp",
  "title": "UniFi MCP",
  "version": "1.0.1",
  "packages": [{
    "registryType": "pypi",
    "identifier": "mcp-unifi",
    "runtimeHint": "uvx",
    "transport": {"type": "stdio"}
  }]
}
```

## CHANGELOG.md

Every version bump must have a corresponding CHANGELOG entry following [Keep a Changelog](https://keepachangelog.com/) format.

## See Also

- [CICD.md](CICD.md) — CI/CD workflow details
- [CHECKLIST](../CHECKLIST.md) — Pre-release checklist
