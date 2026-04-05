# Environment Variable Reference

Machine-oriented reference for all environment variables consumed by unifi-mcp.

## Required

```env
UNIFI_URL=https://192.168.1.1:443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=secret
```

## Conditional

```env
# Required unless UNIFI_MCP_NO_AUTH=true
UNIFI_MCP_TOKEN=64-char-hex-string
```

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
