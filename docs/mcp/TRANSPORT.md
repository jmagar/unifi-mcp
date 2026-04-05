# Transport Methods Reference

## Overview

unifi-mcp supports two transport methods for MCP communication:

| Transport | Use Case | Auth | Port |
|-----------|----------|------|------|
| HTTP (streamable) | Docker, remote access, plugin | Bearer token | 8001 |
| stdio | Claude Desktop, Codex CLI | Process isolation | N/A |

## HTTP Transport (Default)

Set `UNIFI_MCP_TRANSPORT=http` (default).

The server runs as a FastMCP HTTP application behind Uvicorn, wrapped in a Starlette app with bearer auth middleware. The MCP endpoint is at `/mcp`.

### Endpoints

| Path | Method | Auth | Description |
|------|--------|------|-------------|
| `/health` | GET | none | Health check |
| `/mcp` | POST | Bearer | MCP JSON-RPC endpoint |

### Request Format

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'
```

### Docker Deployment

HTTP transport is the standard for Docker deployments. The container exposes port 8001 and requires `UNIFI_MCP_TOKEN` for authentication.

```yaml
services:
  unifi-mcp:
    build: .
    ports:
      - "8001:8001"
    env_file: .env
```

## stdio Transport

Set `UNIFI_MCP_TRANSPORT=stdio`.

The server communicates via stdin/stdout using the MCP stdio protocol. No HTTP server is started, no port is bound, and no bearer token is needed.

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "unifi-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "unifi_mcp.main"],
      "env": {
        "UNIFI_URL": "https://192.168.1.1:443",
        "UNIFI_USERNAME": "admin",
        "UNIFI_PASSWORD": "secret",
        "UNIFI_MCP_TRANSPORT": "stdio",
        "UNIFI_MCP_NO_AUTH": "true"
      }
    }
  }
}
```

### Gemini Extension Configuration

```json
{
  "mcpServers": {
    "unifi-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "unifi_mcp.main"],
      "cwd": "${extensionPath}"
    }
  }
}
```

### Security

stdio transport relies on process isolation. Only the parent process can communicate with the server. No bearer token is required; set `UNIFI_MCP_NO_AUTH=true`.

## Choosing a Transport

| Scenario | Recommended Transport |
|----------|----------------------|
| Docker Compose deployment | HTTP |
| Claude Code plugin (remote server) | HTTP |
| Claude Desktop (local) | stdio |
| Codex CLI (local) | stdio |
| Behind reverse proxy (SWAG, Caddy) | HTTP |
| CI/CD testing | HTTP |

## See Also

- [AUTH.md](AUTH.md) — Authentication per transport
- [CONNECT.md](CONNECT.md) — Client connection guides
- [DEPLOY.md](DEPLOY.md) — Deployment patterns
