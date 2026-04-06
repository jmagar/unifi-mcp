# Environment Variable Reference

Machine-oriented reference for all environment variables consumed by unifi-mcp.

## Deployment paths

unifi-mcp supports two deployment models:

### Path 1 — Claude Code Plugin (stdio)

- Transport: `stdio` (Claude Code spawns the process)
- Credentials: stored in `plugin.json` userConfig, interpolated via `${userConfig.*}` in `.mcp.json`
- Auth: disabled (`UNIFI_MCP_NO_AUTH=true`)
- Config file: `.mcp.json`

### Path 2 — Docker Compose (HTTP)

- Transport: `http` (FastMCP server on a port)
- Credentials: stored in `.env` file alongside `docker-compose.yaml`
- Auth: bearer token required (`UNIFI_MCP_TOKEN`)
- Config file: `.env`

## Required

| Variable | Description | Stdio | HTTP |
|----------|-------------|-------|------|
| `UNIFI_URL` | Controller URL with port (e.g., `https://192.168.1.1:443`) | required | required |
| `UNIFI_USERNAME` | Local admin username (not UniFi Cloud SSO) | required | required |
| `UNIFI_PASSWORD` | Local admin password | required | required |
| `UNIFI_MCP_TOKEN` | Bearer token for HTTP auth | not needed | required |

## Controller Options

```env
UNIFI_IS_UDM_PRO=true           # true = UDM Pro/SE/Cloud Gateway Max; false = legacy
UNIFI_VERIFY_SSL=false           # true = verify SSL; false = skip (self-signed)
UNIFI_CONTROLLER_URL=            # Legacy alias for UNIFI_URL
```

## Server Configuration

```env
UNIFI_MCP_HOST=0.0.0.0          # Bind address
UNIFI_MCP_PORT=8001              # HTTP port
UNIFI_MCP_TRANSPORT=http         # http or stdio
UNIFI_MCP_NO_AUTH=false          # true = disable bearer auth
UNIFI_MCP_LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR
UNIFI_MCP_LOG_FILE=/tmp/unifi-mcp.log  # Log file (auto-clears at 10 MB)
```

## Legacy Server Variables

```env
UNIFI_LOCAL_MCP_HOST=            # Alias for UNIFI_MCP_HOST
UNIFI_LOCAL_MCP_PORT=            # Alias for UNIFI_MCP_PORT
UNIFI_LOCAL_MCP_LOG_LEVEL=       # Alias for UNIFI_MCP_LOG_LEVEL
UNIFI_LOCAL_MCP_LOG_FILE=        # Alias for UNIFI_MCP_LOG_FILE
NO_AUTH=                         # Alias for UNIFI_MCP_NO_AUTH
```

## Safety Gates

```env
UNIFI_MCP_ALLOW_DESTRUCTIVE=false  # true = auto-confirm destructive ops
UNIFI_MCP_ALLOW_YOLO=false         # true = skip all safety prompts
ALLOW_DESTRUCTIVE=                  # Legacy alias
ALLOW_YOLO=                         # Legacy alias
```

## Docker

```env
PUID=1000                        # Container user ID
PGID=1000                        # Container group ID
DOCKER_NETWORK=jakenet           # Docker network name
UNIFI_MCP_VOLUME=unifi-mcp-data  # Data volume name
RUNNING_IN_DOCKER=false          # Rewrites localhost -> host.docker.internal
```

## Variable Resolution Order

For variables with legacy aliases, the resolution order is:

1. Canonical name (e.g., `UNIFI_MCP_PORT`)
2. Legacy alias (e.g., `UNIFI_LOCAL_MCP_PORT`)
3. Default value

## See Also

- [CONFIG](../CONFIG.md) — Human-oriented configuration reference
- [AUTH.md](AUTH.md) — Authentication details
