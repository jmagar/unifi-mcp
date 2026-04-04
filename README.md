# UniFi MCP

FastMCP server for local UniFi controller management. The repo exposes a single `unifi` action router plus discovery/help tooling for devices, clients, network configuration, and controller monitoring.

## What this repository ships

- `unifi_mcp/`: server, formatters, resources, and tool modules
- `skills/unifi/`: client-facing UniFi skill
- `docs/`: API notes, action-pattern docs, testing notes, and formatting references
- `.claude-plugin/`, `.codex-plugin/`, `gemini-extension.json`: client manifests
- `docker-compose.yaml`, `Dockerfile`: container deployment
- `tests/`: unit, resource, and integration tests

## MCP surface

### Main tools

| Tool | Purpose |
| --- | --- |
| `unifi` | Action router for controller, client, device, and network operations |
| `unifi_help` | Markdown help for all actions and parameters |

### Supported action groups

| Group | Actions |
| --- | --- |
| Device management | `get_devices`, `get_device_by_mac`, `restart_device`, `locate_device` |
| Client management | `get_clients`, `reconnect_client`, `block_client`, `unblock_client`, `forget_client`, `set_client_name`, `set_client_note` |
| Network config | `get_sites`, `get_wlan_configs`, `get_network_configs`, `get_port_configs`, `get_port_forwarding_rules`, `get_firewall_rules`, `get_firewall_groups`, `get_static_routes` |
| Monitoring | `get_controller_status`, `get_events`, `get_alarms`, `get_dpi_stats`, `get_rogue_aps`, `start_spectrum_scan`, `get_spectrum_scan_state`, `authorize_guest`, `get_speedtest_results`, `get_ips_events` |
| Identity | `get_user_info` |

Destructive actions such as `restart_device`, `block_client`, `forget_client`, and `reconnect_client` require confirmation unless the server is explicitly configured to allow them.

## Installation

### Marketplace

```bash
/plugin marketplace add jmagar/claude-homelab
/plugin install unifi-mcp @jmagar-claude-homelab
```

### Local development

```bash
uv sync
uv run python -m unifi_mcp.main
```

Console script entrypoints from `pyproject.toml`:

```bash
uv run unifi-mcp
uv run unifi-local-mcp
```

## Configuration

Create `.env` from `.env.example` and set:

```bash
UNIFI_URL=https://192.168.1.1:443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your_password_here
UNIFI_IS_UDM_PRO=true
UNIFI_VERIFY_SSL=false
UNIFI_MCP_HOST=0.0.0.0
UNIFI_MCP_PORT=8001
UNIFI_MCP_TRANSPORT=http
UNIFI_MCP_TOKEN=...
UNIFI_MCP_NO_AUTH=false
UNIFI_MCP_ALLOW_YOLO=false
UNIFI_MCP_ALLOW_DESTRUCTIVE=false
UNIFI_MCP_LOG_LEVEL=INFO
```

Notes:

- `http` and `stdio` are the supported transports documented in this repo.
- HTTP mode uses Bearer auth unless `UNIFI_MCP_NO_AUTH=true`.
- `UNIFI_VERIFY_SSL=false` is common for self-signed local-controller certificates.

## Typical operations

```text
unifi action=get_clients connected_only=true
unifi action=get_devices
unifi action=get_controller_status
unifi action=get_firewall_rules
unifi action=get_speedtest_results limit=5
unifi_help
```

## Development commands

```bash
just dev
just lint
just fmt
just typecheck
just test
just up
just logs
just health
```

Important recipes:

- `just dev`: run the server locally
- `just build`: editable install with `uv pip install -e .`
- `just check-contract`: skill/server contract lint

## Verification

Recommended:

```bash
just lint
just typecheck
just test
```

If you need a running-server check:

```bash
just health
just test-live
```

## Related files

- `unifi_mcp/server.py`: transport startup and HTTP serving
- `skills/unifi/SKILL.md`: action reference and operational guidance
- `docs/consolidated-action-pattern.md`: rationale for the unified action router
- `docs/testing.md`: test strategy notes

## License

MIT
