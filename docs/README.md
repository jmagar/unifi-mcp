# UniFi MCP

MCP server for UniFi network controller management. Monitor devices, clients, network health, firewall rules, and perform management operations through a unified tool interface.

| | |
|---|---|
| **Version** | 1.0.1 |
| **Registry** | [tv.tootie/unifi-mcp](https://registry.modelcontextprotocol.io/servers/tv.tootie/unifi-mcp) |
| **PyPI** | [mcp-unifi](https://pypi.org/project/mcp-unifi/) |
| **Docker** | `ghcr.io/jmagar/unifi-mcp` |
| **License** | MIT |
| **Language** | Python 3.10+ / FastMCP 2.12 |
| **Transport** | HTTP (streamable) or stdio |
| **Port** | 8001 |

## Tools

| Tool | Purpose |
|------|---------|
| `unifi` | Single action-based tool for all 31 UniFi operations |
| `unifi_help` | Returns markdown reference for all actions and parameters |

The `unifi` tool uses an `action` parameter to dispatch to 31 operations across five domains:

- **Device Management** (4): get_devices, get_device_by_mac, restart_device, locate_device
- **Client Management** (7): get_clients, reconnect_client, block_client, unblock_client, forget_client, set_client_name, set_client_note
- **Network Configuration** (8): get_sites, get_wlan_configs, get_network_configs, get_port_configs, get_port_forwarding_rules, get_firewall_rules, get_firewall_groups, get_static_routes
- **Monitoring** (10): get_controller_status, get_events, get_alarms, get_dpi_stats, get_rogue_aps, start_spectrum_scan, get_spectrum_scan_state, authorize_guest, get_speedtest_results, get_ips_events
- **Authentication** (1): get_user_info

See [TOOLS](mcp/TOOLS.md) for full parameter documentation.

## Quick Start

### Claude Code Plugin

```bash
/plugin marketplace add jmagar/unifi-mcp
```

Configure credentials when prompted (UniFi controller URL, username, password).

### Docker Compose

```bash
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
cp .env.example .env
# Edit .env with your UniFi controller credentials
docker compose up -d
```

### Local Development

```bash
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
uv sync
cp .env.example .env
# Edit .env with your credentials
uv run python -m unifi_mcp.main
```

## Configuration

Required environment variables:

| Variable | Description |
|----------|-------------|
| `UNIFI_URL` | UniFi controller URL (e.g., `https://192.168.1.1:443`) |
| `UNIFI_USERNAME` | Controller admin username |
| `UNIFI_PASSWORD` | Controller admin password |
| `UNIFI_MCP_TOKEN` | Bearer token for MCP auth (generate: `openssl rand -hex 32`) |

See [CONFIG](CONFIG.md) for all variables including optional settings.

## Authentication

Two authentication layers:

1. **Inbound** (MCP clients to this server): Bearer token via `UNIFI_MCP_TOKEN`
2. **Outbound** (this server to UniFi controller): Username/password session auth

UniFi controllers use session-based authentication with username and password, not API keys. The server handles login, CSRF token extraction, and session refresh automatically.

See [AUTH](mcp/AUTH.md) for details.

## Resources

MCP resources provide read-only data access via `unifi://` URIs:

| Resource URI | Description |
|---|---|
| `unifi://overview` | Network overview with device/client counts |
| `unifi://dashboard` | Dashboard metrics (WAN traffic, latency) |
| `unifi://devices` | All devices with status |
| `unifi://clients` | Connected clients |
| `unifi://events` | Recent events |
| `unifi://alarms` | Active alarms |
| `unifi://sites` | All sites |

All resources support site-specific variants: `unifi://devices/{site_name}`.

See [RESOURCES](mcp/RESOURCES.md) for the full list.

## Documentation

| Section | Contents |
|---------|----------|
| [SETUP](SETUP.md) | Step-by-step installation guide |
| [CONFIG](CONFIG.md) | All environment variables |
| [TOOLS](mcp/TOOLS.md) | Tool reference with all 31 actions |
| [AUTH](mcp/AUTH.md) | Authentication details |
| [DEPLOY](mcp/DEPLOY.md) | Docker, local, stdio deployment |
| [TESTS](mcp/TESTS.md) | Testing guide |
| [INVENTORY](INVENTORY.md) | Full component listing |
