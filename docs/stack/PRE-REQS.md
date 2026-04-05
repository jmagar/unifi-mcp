# Prerequisites

Required tools and versions before developing or deploying unifi-mcp.

## Development

| Tool | Version | Install |
|------|---------|---------|
| Python | >= 3.10 | System package manager or [python.org](https://www.python.org/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| just | latest | `cargo install just` or system package manager |
| Git | >= 2.0 | System package manager |

## Docker Deployment

| Tool | Version | Install |
|------|---------|---------|
| Docker | >= 20.10 | [docs.docker.com](https://docs.docker.com/engine/install/) |
| Docker Compose | >= 2.0 | Included with Docker Desktop or `docker-compose-plugin` |

## Optional

| Tool | Version | Purpose |
|------|---------|---------|
| pre-commit | latest | Pre-commit hooks (`uv sync --extra dev && uv run pre-commit install`) |
| curl | any | Manual testing |
| jq | any | JSON formatting |

## UniFi Controller

A running UniFi controller is required:

| Controller | Tested | Notes |
|------------|--------|-------|
| UDM Pro | yes | Set `UNIFI_IS_UDM_PRO=true` |
| UDM SE | yes | Set `UNIFI_IS_UDM_PRO=true` |
| Cloud Gateway Max (UCG Max) | yes | Set `UNIFI_IS_UDM_PRO=true` |
| UniFi Network Application (self-hosted) | partial | Set `UNIFI_IS_UDM_PRO=false`, typically port 8443 |

Requirements:
- Local admin account (not UniFi Cloud SSO)
- Network reachable from the machine running unifi-mcp
- HTTPS access (self-signed certificates are fine with `UNIFI_VERIFY_SSL=false`)

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
uv sync

# Configure
cp .env.example .env
chmod 600 .env
# Edit .env with your credentials

# Run
just dev
```

## See Also

- [SETUP](../SETUP.md) — Full setup guide
- [TECH.md](TECH.md) — Technology choices
