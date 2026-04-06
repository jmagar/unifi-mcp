# Plugin Settings -- unifi-mcp

Plugin configuration and user-facing settings.

## How it works

When installed as a Claude Code plugin, unifi-mcp uses **stdio transport**. Claude Code spawns the server process directly — no HTTP layer, no bearer token needed.

Sensitive credentials are stored in `plugin.json` `userConfig` fields. Claude Code interpolates `${userConfig.*}` references in `.mcp.json` at launch time, passing values as environment variables to the spawned process.

## Configuration layers

| Layer | Source | Managed by |
|-------|--------|------------|
| Plugin userConfig | `.claude-plugin/plugin.json` | Claude Code UI / plugin install |
| .mcp.json env | `.mcp.json` | Checked into repo with defaults + `${userConfig.*}` refs |
| Docker compose | `docker-compose.yaml` + `.env` | Manual `.env` file |

## userConfig fields

| userConfig Key | Environment Variable | Sensitive | Description |
|----------------|---------------------|-----------|-------------|
| `unifi_url` | `UNIFI_URL` | no | UniFi controller URL with port |
| `unifi_username` | `UNIFI_USERNAME` | yes | Controller local admin username |
| `unifi_password` | `UNIFI_PASSWORD` | yes | Controller password (use a dedicated read-only account) |

## Defaults in .mcp.json

Non-sensitive environment variables have sensible defaults hardcoded in `.mcp.json`:

| Variable | Default | Notes |
|----------|---------|-------|
| `UNIFI_MCP_TRANSPORT` | `stdio` | Always stdio for plugin deployment |
| `UNIFI_MCP_NO_AUTH` | `true` | No HTTP auth needed for stdio |
| `UNIFI_IS_UDM_PRO` | `true` | UDM Pro/SE/Cloud Gateway Max mode |
| `UNIFI_VERIFY_SSL` | `false` | Skip SSL verification for self-signed certs |
| `UNIFI_MCP_LOG_LEVEL` | `INFO` | Log level |
| `UNIFI_MCP_ALLOW_YOLO` | `false` | Destructive op safety gate |
| `UNIFI_MCP_ALLOW_DESTRUCTIVE` | `false` | Full destructive bypass |

## Startup hooks

The `sync-uv.sh` SessionStart hook keeps the uv lockfile and persistent Python environment in sync at session start.

## See Also

- [HOOKS.md](HOOKS.md) -- Hook configuration
- [PLUGINS.md](PLUGINS.md) -- Manifest reference
- [../CONFIG.md](../CONFIG.md) -- Full env var reference
