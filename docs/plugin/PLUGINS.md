# Plugin Manifest Reference

Structure and conventions for plugin manifest files in unifi-mcp.

## File Locations

| File | Platform | Purpose |
|------|----------|---------|
| `.claude-plugin/plugin.json` | Claude Code | Plugin manifest with userConfig |
| `.codex-plugin/plugin.json` | Codex | Plugin manifest with interface metadata |
| `gemini-extension.json` | Gemini | Extension with MCP server config |
| `server.json` | MCP Registry | Registry entry |
| `.app.json` | Internal | App metadata |

## Claude Code Plugin (`.claude-plugin/plugin.json`)

Key fields:

```json
{
  "name": "unifi-mcp",
  "version": "1.0.1",
  "description": "UniFi network management via MCP tools.",
  "repository": "https://github.com/jmagar/unifi-mcp",
  "userConfig": {
    "unifi_mcp_url": {"type": "string", "default": "https://unifi.tootie.tv/mcp", "sensitive": false},
    "unifi_mcp_token": {"type": "string", "sensitive": true},
    "unifi_url": {"type": "string", "sensitive": true},
    "unifi_username": {"type": "string", "sensitive": true},
    "unifi_password": {"type": "string", "sensitive": true}
  }
}
```

The `userConfig` section defines credential fields presented during plugin setup. Sensitive fields are stored encrypted.

## Codex Plugin (`.codex-plugin/plugin.json`)

```json
{
  "name": "unifi-mcp",
  "version": "1.0.1",
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "apps": "./.app.json",
  "interface": {
    "displayName": "UniFi MCP",
    "category": "Infrastructure",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "List UniFi devices on my network.",
      "Show active UniFi clients.",
      "Check UniFi alerts and controller health."
    ],
    "brandColor": "#0559C9"
  }
}
```

## Gemini Extension (`gemini-extension.json`)

```json
{
  "name": "unifi-mcp",
  "version": "1.0.1",
  "mcpServers": {
    "unifi-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "unifi_mcp.main"],
      "cwd": "${extensionPath}"
    }
  }
}
```

Uses stdio transport when run as a Gemini extension.

## MCP Registry (`server.json`)

```json
{
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

## Version Sync

All manifest files must have the same version. This is enforced by:
- The `version-sync` CI job
- The `just publish` recipe (bumps all files simultaneously)

## See Also

- [CONFIG.md](CONFIG.md) — Plugin settings
- [MARKETPLACES.md](MARKETPLACES.md) — Publishing
