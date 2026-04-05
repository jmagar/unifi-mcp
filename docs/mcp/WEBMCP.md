# Web MCP Integration

Browser-accessible MCP endpoints for monitoring and administration.

## HTTP Endpoints

| Path | Method | Auth | Description |
|------|--------|------|-------------|
| `/health` | GET | none | Health check — JSON status |
| `/mcp` | POST | Bearer | MCP JSON-RPC endpoint |

## Health Endpoint

Always accessible without authentication. Used by Docker healthchecks, load balancers, and monitoring tools.

```bash
curl -sf http://localhost:8001/health
```

```json
{
  "status": "ok",
  "service": "unifi-mcp",
  "timestamp": "2026-04-04T00:00:00.000000+00:00"
}
```

## MCP Endpoint

Standard MCP JSON-RPC over HTTP. Requires bearer token authentication.

### Tool Call

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'
```

### Tool List

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
```

### Resource Read

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"resources/read","params":{"uri":"unifi://overview"}}'
```

## CORS

CORS is not configured by default. When deploying behind a reverse proxy for browser access, configure CORS at the proxy level.

## Reverse Proxy

For browser access via SWAG or similar:

```nginx
location /mcp {
    proxy_pass http://unifi-mcp:8001/mcp;
    proxy_set_header Authorization $http_authorization;
    proxy_buffering off;
}
```

## See Also

- [TRANSPORT.md](TRANSPORT.md) — Transport configuration
- [AUTH.md](AUTH.md) — Authentication
- [DEPLOY.md](DEPLOY.md) — Reverse proxy setup
