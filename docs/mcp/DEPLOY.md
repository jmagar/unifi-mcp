# Deployment Guide

Deployment patterns for unifi-mcp. Choose the method that fits your environment.

## Docker Compose (Recommended)

```bash
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
cp .env.example .env
# Edit .env with your credentials
docker compose up -d
```

The compose file uses:
- Multi-stage build with Python 3.11 slim
- Non-root user (UID 1000)
- `env_file: ~/.claude-homelab/.env` for credentials
- Health check via `wget` to `/health`
- Memory limit: 1024 MB, CPU limit: 1.0
- External Docker network (`jakenet` by default)

### Docker Image

Pre-built images available from GitHub Container Registry:

```bash
docker pull ghcr.io/jmagar/unifi-mcp:latest
```

Tags: `latest`, `main`, `v1.0.1`, `1.0`, `1`, `sha-<commit>`

Platforms: `linux/amd64`, `linux/arm64`

## Local Development

```bash
uv sync
uv run python -m unifi_mcp.main
```

Or via Justfile:

```bash
just dev
```

The server binds to `0.0.0.0:8001` by default. Override with `UNIFI_MCP_HOST` and `UNIFI_MCP_PORT`.

## stdio Mode

For Claude Desktop or Codex CLI local usage:

```bash
UNIFI_MCP_TRANSPORT=stdio UNIFI_MCP_NO_AUTH=true uv run python -m unifi_mcp.main
```

No HTTP server is started. Communication happens via stdin/stdout.

## ASGI Deployment

For production deployments with Gunicorn or other ASGI servers:

```python
from unifi_mcp.main import create_app
app = create_app()
```

```bash
gunicorn unifi_mcp.main:create_app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## Reverse Proxy (SWAG)

When deploying behind SWAG with Nginx:

```nginx
server {
    listen 443 ssl;
    server_name unifi-mcp.yourdomain.com;

    location / {
        proxy_pass http://unifi-mcp:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }
}
```

Set `UNIFI_MCP_NO_AUTH=true` if the proxy handles authentication (Authelia, Cloudflare Access).

## Health Monitoring

The `/health` endpoint returns:

```json
{"status": "ok", "service": "unifi-mcp", "timestamp": "2026-04-04T00:00:00+00:00"}
```

Docker healthcheck configured in both Dockerfile and compose:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -q --spider http://localhost:8001/health || exit 1"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 30s
```

## See Also

- [TRANSPORT.md](TRANSPORT.md) — HTTP vs stdio
- [CONNECT.md](CONNECT.md) — Client connection guides
- [CONFIG](../CONFIG.md) — Environment variables
