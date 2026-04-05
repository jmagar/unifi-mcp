# Plugin Settings

Plugin configuration, user-facing settings, and environment sync for unifi-mcp.

## Configuration Layers

| Layer | Source | Priority |
|-------|--------|----------|
| Plugin userConfig | Claude Code UI | Highest — synced to .env at session start |
| `.env` file | Project root | Medium — loaded by python-dotenv |
| System environment | Shell/Docker | Lowest — fallback |

## userConfig Fields

Defined in `.claude-plugin/plugin.json`:

| Key | Type | Sensitive | Description |
|-----|------|-----------|-------------|
| `unifi_mcp_url` | string | no | MCP endpoint URL (default: `https://unifi.tootie.tv/mcp`) |
| `unifi_mcp_token` | string | yes | Bearer token for MCP auth |
| `unifi_url` | string | yes | UniFi controller URL |
| `unifi_username` | string | yes | Controller admin username |
| `unifi_password` | string | yes | Controller admin password |

## Environment Sync

The `sync-env.sh` hook runs at `SessionStart` and copies userConfig values into `.env`:

1. Reads userConfig values from the plugin framework
2. Writes them to `.env` in the project root
3. Ensures `.env` has `chmod 600` permissions

This means users configure credentials once through the plugin UI and they are available to the server process.

## Codex Settings

Defined in `gemini-extension.json` `settings` array:

| Setting | Env Var | Sensitive |
|---------|---------|-----------|
| UniFi Controller URL | `UNIFI_URL` | no |
| UniFi Username | `UNIFI_USERNAME` | no |
| UniFi Password | `UNIFI_PASSWORD` | yes |
| UDM Pro Mode | `UNIFI_IS_UDM_PRO` | no |

## See Also

- [HOOKS.md](HOOKS.md) — Hook configuration
- [PLUGINS.md](PLUGINS.md) — Manifest reference
- [CONFIG](../CONFIG.md) — Full env var reference
