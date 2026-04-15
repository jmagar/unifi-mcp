# Configuration Reference

All environment variables for unifi-mcp, grouped by function.

## Environment File

The `.env` file lives in the project root (or `~/.claude-homelab/.env` for homelab integration). Use `.env.example` as a template.

```bash
cp .env.example .env
chmod 600 .env
```

## UniFi Controller Credentials

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_URL` | yes | — | Controller URL with port (e.g., `https://192.168.1.1:443`) |
| `UNIFI_USERNAME` | yes | — | Local admin username (not UniFi Cloud SSO) |
| `UNIFI_PASSWORD` | yes | — | Local admin password |
| `UNIFI_CONTROLLER_URL` | no | — | Legacy alias for `UNIFI_URL` |

## Controller Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_IS_UDM_PRO` | no | `true` | Set `true` for UDM Pro/SE/Cloud Gateway Max; `false` for legacy controllers |
| `UNIFI_VERIFY_SSL` | no | `false` | Enable SSL certificate verification; `false` for self-signed certs |

### UDM Pro Detection

When `UNIFI_IS_UDM_PRO=true`:
- API base path: `/proxy/network/api`
- Login endpoint: `/api/auth/login`
- Session cookie: `TOKEN` (JWT with CSRF token in payload)
- Controller status: `/api/system` (UniFi OS system endpoint)

When `UNIFI_IS_UDM_PRO=false`:
- API base path: `/api`
- Login endpoint: `/api/login`
- Session cookie: `unifises`
- Controller status: `/api/status`

## MCP Server Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_MCP_HOST` | no | `0.0.0.0` | Bind address |
| `UNIFI_MCP_PORT` | no | `8001` | HTTP port |
| `UNIFI_MCP_TRANSPORT` | no | `http` | Transport: `http` or `stdio` |
| `UNIFI_MCP_TOKEN` | conditional | — | Bearer token for HTTP auth; required unless `UNIFI_MCP_NO_AUTH=true` |
| `UNIFI_MCP_NO_AUTH` | no | `false` | Disable bearer auth (proxy-managed environments only) |
| `UNIFI_MCP_LOG_LEVEL` | no | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `UNIFI_MCP_LOG_FILE` | no | `/tmp/unifi-mcp.log` | Log file path (auto-clears at 10 MB) |

### Legacy Variable Names

These are accepted as fallbacks for backward compatibility:

| Legacy | Current |
|--------|---------|
| `UNIFI_LOCAL_MCP_HOST` | `UNIFI_MCP_HOST` |
| `UNIFI_LOCAL_MCP_PORT` | `UNIFI_MCP_PORT` |
| `UNIFI_LOCAL_MCP_LOG_LEVEL` | `UNIFI_MCP_LOG_LEVEL` |
| `UNIFI_LOCAL_MCP_LOG_FILE` | `UNIFI_MCP_LOG_FILE` |
| `NO_AUTH` | `UNIFI_MCP_NO_AUTH` |

## Destructive Operation Safety

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_MCP_ALLOW_DESTRUCTIVE` | no | `false` | Auto-confirm all destructive ops |
| `UNIFI_MCP_ALLOW_YOLO` | no | `false` | Skip elicitation prompts entirely |
| `ALLOW_DESTRUCTIVE` | no | `false` | Legacy alias for `UNIFI_MCP_ALLOW_DESTRUCTIVE` |
| `ALLOW_YOLO` | no | `false` | Legacy alias for `UNIFI_MCP_ALLOW_YOLO` |

Destructive actions (restart_device, block_client, forget_client, reconnect_client) require one of:
1. `confirm=true` parameter on the tool call
2. `UNIFI_MCP_ALLOW_DESTRUCTIVE=true` in the environment
3. `UNIFI_MCP_ALLOW_YOLO=true` in the environment

## Docker Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PUID` | no | `1000` | Container user ID |
| `PGID` | no | `1000` | Container group ID |
| `DOCKER_NETWORK` | no | `unifi-mcp` | Docker network name |
| `UNIFI_MCP_VOLUME` | no | `unifi-mcp-data` | Data volume name |
| `RUNNING_IN_DOCKER` | no | `false` | Rewrites `localhost` to `host.docker.internal` in service URLs |

## Plugin userConfig

When installed as a Claude Code plugin, these fields are presented to the user during setup:

| userConfig Key | Maps To | Sensitive |
|----------------|---------|-----------|
| `unifi_mcp_url` | MCP endpoint URL | no |
| `unifi_mcp_token` | `UNIFI_MCP_TOKEN` | yes |
| `unifi_url` | `UNIFI_URL` | yes |
| `unifi_username` | `UNIFI_USERNAME` | yes |
| `unifi_password` | `UNIFI_PASSWORD` | yes |

userConfig values must be set manually in `.env`.

## See Also

- [ENV](mcp/ENV.md) — Machine-oriented env var reference
- [AUTH](mcp/AUTH.md) — Authentication flow details
- [SETUP](SETUP.md) — Installation walkthrough
