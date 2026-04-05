# Marketplace Publishing

Registration and publishing patterns for Claude, Codex, Gemini, and MCP Registry marketplaces.

## Marketplace Locations

| Marketplace | Manifest | Identifier |
|-------------|----------|------------|
| Claude Code | `.claude-plugin/plugin.json` | `jmagar/unifi-mcp` |
| Codex | `.codex-plugin/plugin.json` | `jmagar/unifi-mcp` |
| Gemini | `gemini-extension.json` | `unifi-mcp` |
| MCP Registry | `server.json` | `tv.tootie/unifi-mcp` |
| PyPI | `pyproject.toml` | `mcp-unifi` |
| Docker (GHCR) | `Dockerfile` | `ghcr.io/jmagar/unifi-mcp` |

## Claude Code Plugin

Install via marketplace:

```bash
/plugin marketplace add jmagar/unifi-mcp
```

The plugin is discovered from the GitHub repository. Claude Code reads `.claude-plugin/plugin.json` for metadata, hooks, and userConfig.

## Codex Plugin

The Codex plugin manifest provides interface metadata (display name, description, brand color, default prompts) and references skills and MCP server configuration.

## Gemini Extension

The Gemini extension runs the MCP server locally via stdio transport using `uv run`.

## MCP Registry

Published to `tv.tootie/unifi-mcp` using DNS authentication on `tootie.tv`. The registry entry points to the PyPI package `mcp-unifi` with `uvx` runtime hint.

### Publishing

Automated via the `publish-pypi.yml` workflow:

1. Build package
2. Publish to PyPI
3. Authenticate to MCP Registry via DNS
4. Publish `server.json` to registry

## PyPI

Package name: `mcp-unifi`

Install and run:

```bash
uvx mcp-unifi
```

## Docker

Pre-built images at `ghcr.io/jmagar/unifi-mcp`:

```bash
docker pull ghcr.io/jmagar/unifi-mcp:latest
```

## See Also

- [PUBLISH](../mcp/PUBLISH.md) — Publishing workflow details
- [PLUGINS.md](PLUGINS.md) — Manifest reference
