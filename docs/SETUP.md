# Setup Guide

Step-by-step instructions to get unifi-mcp running locally, in Docker, or as a Claude Code plugin.

## Prerequisites

- Python 3.10+ with [uv](https://docs.astral.sh/uv/) (local development)
- Docker and Docker Compose (container deployment)
- A UniFi controller (UDM Pro, UDM SE, Cloud Gateway Max, or legacy controller)
- Local admin credentials for the controller (not UniFi Cloud SSO)

## 1. Clone and Install

```bash
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
uv sync
```

## 2. Configure Environment

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env` with your controller credentials:

```env
UNIFI_URL=https://192.168.1.1:443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your_password_here
UNIFI_IS_UDM_PRO=true
UNIFI_VERIFY_SSL=false
UNIFI_MCP_TOKEN=$(openssl rand -hex 32)
```

### Determining Controller Type

Set `UNIFI_IS_UDM_PRO=true` for:
- UniFi Dream Machine Pro (UDM Pro)
- UniFi Dream Machine SE (UDM SE)
- UniFi Cloud Gateway Max (UCG Max)
- Any device running UniFi OS

Set `UNIFI_IS_UDM_PRO=false` for:
- Self-hosted UniFi Network Application (Java-based)
- Running on Debian/Ubuntu or in a Docker container
- Typically accessed on port 8443

This setting changes:
- API base path (`/proxy/network/api` vs `/api`)
- Login endpoint (`/api/auth/login` vs `/api/login`)
- Session cookie handling (`TOKEN` JWT vs `unifises` cookie)

### SSL Verification

Set `UNIFI_VERIFY_SSL=false` for self-signed certificates (most homelab setups). Set to `true` if you have a valid certificate on the controller.

## 3. Generate Bearer Token

```bash
openssl rand -hex 32
```

Copy the output into `UNIFI_MCP_TOKEN` in `.env`. This token authenticates MCP clients to the server. Generate a unique token; do not reuse tokens from other services.

## 4. Start the Server

### Option A: Local Development

```bash
uv run python -m unifi_mcp.main
```

Or via Justfile:

```bash
just dev
```

### Option B: Docker Compose

```bash
docker compose up -d
```

### Option C: Claude Code Plugin

```bash
/plugin marketplace add jmagar/unifi-mcp
```

When prompted, enter your UniFi controller URL, username, password, and MCP token.

## 5. Verify

### Health Check

```bash
curl -sf http://localhost:8001/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "ok",
  "service": "unifi-mcp",
  "timestamp": "2026-04-04T00:00:00.000000+00:00"
}
```

### Test Tool Call

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'
```

### Run Tests

```bash
just test
```

## Troubleshooting

### "UNIFI_URL environment variable is required"

The `.env` file is not being loaded. Verify it exists in the project root and contains `UNIFI_URL=`.

### "Authentication failed with status 401"

- Check username and password are correct
- Ensure you are using a local admin account, not a UniFi Cloud (SSO) account
- Verify the controller URL is correct and reachable

### "UNIFI_MCP_TOKEN must be set"

Either set `UNIFI_MCP_TOKEN` in `.env` or set `UNIFI_MCP_NO_AUTH=true` for local testing behind a trusted proxy.

### SSL errors

Set `UNIFI_VERIFY_SSL=false` in `.env` if using self-signed certificates.

### Connection refused

- Verify the UniFi controller is running and the URL is reachable
- For Docker deployments, ensure the container can reach the controller (check Docker network settings)
- If the controller is on localhost, set `RUNNING_IN_DOCKER=true` to auto-rewrite localhost to `host.docker.internal`

## See Also

- [CONFIG](CONFIG.md) — All environment variables
- [AUTH](mcp/AUTH.md) — Authentication details
- [DEPLOY](mcp/DEPLOY.md) — Deployment patterns
