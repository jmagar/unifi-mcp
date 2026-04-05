# Authentication Reference

## Overview

unifi-mcp has two authentication boundaries:

1. **Inbound** — MCP clients authenticating to the MCP server
2. **Outbound** — MCP server authenticating to the UniFi controller

## Inbound Authentication (Client to MCP Server)

### Bearer Token

All HTTP requests to the MCP server require a bearer token:

```
Authorization: Bearer {UNIFI_MCP_TOKEN}
```

The token is set via the `UNIFI_MCP_TOKEN` environment variable. Generate one with:

```bash
openssl rand -hex 32
```

### BearerAuthMiddleware

The server validates inbound tokens using `BearerAuthMiddleware`:

```
Request -> BearerAuthMiddleware -> Route Handler
                |
                v (401/403)
          Missing/invalid token
```

- Returns `401 Unauthorized` if the Authorization header is missing or not `Bearer` format
- Returns `403 Forbidden` if the token does not match (timing-safe comparison via `hmac.compare_digest`)
- Applies to all routes except `/health`

### Unauthenticated Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check — returns `{"status": "ok", "service": "unifi-mcp", "timestamp": "..."}` |

The health endpoint is intentionally unauthenticated so load balancers, Docker healthchecks, and monitoring can probe without credentials.

### No-Auth Mode

When running behind a reverse proxy that handles authentication (SWAG with Authelia, Cloudflare Access):

```env
UNIFI_MCP_NO_AUTH=true
```

This disables `BearerAuthMiddleware` entirely. The middleware passes all requests through without checking tokens. Only use when the proxy enforces its own auth layer.

### stdio Transport

stdio transport does not use bearer tokens. Process-level isolation provides the security boundary — only the parent process (Claude Desktop, Codex CLI) can communicate with the server.

## Outbound Authentication (MCP Server to UniFi Controller)

### Session-Based Auth (Username/Password)

UniFi controllers use session-based authentication, not API keys. The server sends username and password to the login endpoint, receives a session cookie, and uses it for subsequent requests.

```env
UNIFI_URL=https://192.168.1.1:443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your_password_here
```

**Important**: Use a local admin account. UniFi Cloud (SSO) accounts are not supported for direct controller API access.

### UDM Pro Authentication Flow

When `UNIFI_IS_UDM_PRO=true`:

1. POST `{UNIFI_URL}/api/auth/login` with `{"username": "...", "password": "..."}`
2. Server receives `TOKEN` cookie containing a JWT
3. JWT payload is decoded to extract `csrfToken`
4. All subsequent requests include `X-CSRF-Token: {csrfToken}` header
5. Cookies are managed automatically by the httpx session

### Legacy Controller Authentication Flow

When `UNIFI_IS_UDM_PRO=false`:

1. POST `{UNIFI_URL}/api/login` with `{"username": "...", "password": "...", "remember": true}`
2. Server receives `unifises` session cookie
3. CSRF token extracted from response headers
4. Cookies are managed automatically by the httpx session

### Session Management

- `ensure_authenticated()` is called before every API request
- On 401 response, the client automatically reauthenticates and retries the request once
- Sessions time out after controller-defined intervals (typically 30 minutes)
- The client handles reauthentication transparently

### SSL Verification

```env
UNIFI_VERIFY_SSL=false   # Default — self-signed certs (most homelabs)
UNIFI_VERIFY_SSL=true    # Valid certificate on controller
```

The httpx client is initialized with `verify=config.verify_ssl`. Set to `false` for self-signed certificates common in homelab setups.

## Plugin userConfig Integration

When installed as a Claude Code plugin, credentials are managed via `userConfig` in `plugin.json`:

```json
{
  "userConfig": {
    "unifi_mcp_url": {
      "description": "Full MCP endpoint URL including /mcp path",
      "default": "https://unifi.tootie.tv/mcp",
      "sensitive": false
    },
    "unifi_mcp_token": {
      "description": "Bearer token for MCP authentication",
      "sensitive": true
    },
    "unifi_url": {
      "description": "URL of your UniFi controller",
      "sensitive": true
    },
    "unifi_username": {
      "description": "UniFi controller admin username",
      "sensitive": true
    },
    "unifi_password": {
      "description": "UniFi controller admin password",
      "sensitive": true
    }
  }
}
```

Fields marked `"sensitive": true` are stored encrypted and synced to `.env` by the `sync-env.sh` hook at session start.

## Security Best Practices

- **Never log credentials** — not even at DEBUG level
- **Use `compare_digest()`** — the server already does this for bearer token comparison
- **Rotate credentials regularly** — update `.env` and restart the server
- **Use HTTPS** — the controller URL should use HTTPS (port 443 for UDM Pro, 8443 for legacy)
- **Dedicated admin account** — create a dedicated local admin for MCP, not a personal account
- **Minimal permissions** — the MCP server only needs read access for most operations; destructive ops require explicit confirmation

## See Also

- [ENV.md](ENV.md) — Full environment variable reference
- [TRANSPORT.md](TRANSPORT.md) — Transport-specific auth behavior
- [GUARDRAILS](../GUARDRAILS.md) — Security guardrails
