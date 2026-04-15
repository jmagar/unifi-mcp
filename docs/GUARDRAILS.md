# Security Guardrails

Safety and security patterns enforced across unifi-mcp.

## Credential Management

### Storage

- Credentials live in `.env` (project root or `~/.claude-homelab/.env`)
- `.env` is gitignored and dockerignored
- File permissions: `chmod 600 .env`

### Environment Variables

- `UNIFI_PASSWORD` contains the controller password in plaintext — never log it
- `UNIFI_MCP_TOKEN` is the bearer token — use `compare_digest()` for timing-safe comparison
- Generate tokens with `openssl rand -hex 32` — never reuse tokens across services

### Plugin userConfig

Sensitive fields in `plugin.json` are marked `"sensitive": true`:
- `unifi_mcp_token`
- `unifi_url`
- `unifi_username`
- `unifi_password`

Values are stored encrypted by the plugin framework and must be set manually in `.env`.

## Docker Security

### Dockerfile

- Multi-stage build: builder stage installs dependencies, runtime stage copies only the venv
- Non-root user: `USER unifi` (UID 1000)
- No secrets baked into the image — all credentials come from `env_file` at runtime
- Health check uses `wget` against `/health` (unauthenticated endpoint)

### Compose

- `env_file: ~/.claude-homelab/.env` — no `environment:` block to prevent env baking
- Memory limit: 1024 MB
- CPU limit: 1.0

## Authentication

### Inbound (MCP Clients)

- Bearer token required on all routes except `/health`
- `BearerAuthMiddleware` uses `hmac.compare_digest()` for timing-safe comparison
- Returns 401 for missing/malformed tokens, 403 for invalid tokens
- Disabled via `UNIFI_MCP_NO_AUTH=true` only when behind a proxy with its own auth

### Outbound (UniFi Controller)

- Session-based auth with username/password
- CSRF token extracted from JWT payload (UDM Pro) or response headers (legacy)
- Auto-reauthentication on 401 responses
- SSL verification configurable via `UNIFI_VERIFY_SSL`

## Destructive Operations

Four actions are classified as destructive:
- `restart_device` — reboots a network device
- `block_client` — blocks a client from network access
- `forget_client` — permanently removes client history
- `reconnect_client` — forcibly disconnects and reconnects a client

### Confirmation Gate

Destructive actions require explicit confirmation through one of three paths:

1. **Parameter**: `confirm=true` on the tool call
2. **Environment**: `UNIFI_MCP_ALLOW_DESTRUCTIVE=true`
3. **YOLO mode**: `UNIFI_MCP_ALLOW_YOLO=true` (skips all safety prompts)

Without confirmation, the server returns a `confirmation_required` error with instructions.

### Safety Defaults

- `UNIFI_MCP_ALLOW_DESTRUCTIVE=false` by default
- `UNIFI_MCP_ALLOW_YOLO=false` by default
- These should only be set to `true` in CI/testing environments

## Response Safety

- Response size capped at 512 KB; larger responses are truncated with `... [truncated]`
- Rogue AP results capped at 50 entries to prevent oversized responses
- DPI stats use `format_data_values()` to sanitize raw byte values

## Input Validation

- MAC addresses normalized via `normalize_mac()`: lowercase, colon-separated
- `UnifiParams` Pydantic model validates all parameters before execution
- `limit` must be positive; `minutes` must be positive
- `by_filter` restricted to `by_app` or `by_cat`
- `up_bandwidth`, `down_bandwidth`, `quota` must be non-negative

## See Also

- [AUTH](mcp/AUTH.md) — Authentication reference
- [CONFIG](CONFIG.md) — Environment variable reference
- [TESTS](mcp/TESTS.md) — Testing guide
