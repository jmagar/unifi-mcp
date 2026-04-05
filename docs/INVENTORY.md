# Component Inventory

Complete listing of all unifi-mcp components.

## MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `unifi` | `action` (required), `site_name`, `mac`, `limit`, `connected_only`, `active_only`, `by_filter`, `name`, `note`, `minutes`, `up_bandwidth`, `down_bandwidth`, `quota`, `confirm` | Unified action-based tool for all 31 UniFi operations |
| `unifi_help` | _(none)_ | Returns markdown reference for all actions and parameters |

## Tool Actions (31 total)

### Device Management (4)

| Action | MAC Required | Destructive | Description |
|--------|-------------|-------------|-------------|
| `get_devices` | no | no | List all devices on a site |
| `get_device_by_mac` | yes | no | Get device details by MAC |
| `restart_device` | yes | yes | Restart a device |
| `locate_device` | yes | no | Activate locate LED |

### Client Management (7)

| Action | MAC Required | Destructive | Description |
|--------|-------------|-------------|-------------|
| `get_clients` | no | no | List clients (connected_only default: true) |
| `reconnect_client` | yes | yes | Force client reconnection |
| `block_client` | yes | yes | Block a client |
| `unblock_client` | yes | no | Unblock a client |
| `forget_client` | yes | yes | Remove client history |
| `set_client_name` | yes | no | Set alias name (requires `name` param) |
| `set_client_note` | yes | no | Set note (requires `note` param) |

### Network Configuration (8)

| Action | MAC Required | Destructive | Description |
|--------|-------------|-------------|-------------|
| `get_sites` | no | no | List all sites |
| `get_wlan_configs` | no | no | List WLAN configurations |
| `get_network_configs` | no | no | List network/VLAN configurations |
| `get_port_configs` | no | no | List port profiles |
| `get_port_forwarding_rules` | no | no | List port forwarding rules |
| `get_firewall_rules` | no | no | List firewall rules |
| `get_firewall_groups` | no | no | List firewall groups |
| `get_static_routes` | no | no | List static routes |

### Monitoring and Statistics (10)

| Action | MAC Required | Destructive | Description |
|--------|-------------|-------------|-------------|
| `get_controller_status` | no | no | Controller system info |
| `get_events` | no | no | Recent events (limit default: 100) |
| `get_alarms` | no | no | Alarms (active_only default: true) |
| `get_dpi_stats` | no | no | DPI statistics |
| `get_rogue_aps` | no | no | Rogue access points (limit default: 20, max: 50) |
| `start_spectrum_scan` | yes | no | Start RF spectrum scan |
| `get_spectrum_scan_state` | yes | no | Get spectrum scan results |
| `authorize_guest` | yes | no | Authorize guest access (minutes default: 480) |
| `get_speedtest_results` | no | no | Speed test history (limit default: 20) |
| `get_ips_events` | no | no | IPS/IDS events (limit default: 50) |

### Authentication (1)

| Action | MAC Required | Destructive | Description |
|--------|-------------|-------------|-------------|
| `get_user_info` | no | no | Get authenticated user info (OAuth only) |

## MCP Resources

| URI | Description |
|-----|-------------|
| `unifi://overview` | Network overview (device/client counts, gateway info) |
| `unifi://overview/{site_name}` | Site-specific network overview |
| `unifi://dashboard` | Dashboard metrics (WAN traffic, latency) |
| `unifi://dashboard/{site_name}` | Site-specific dashboard metrics |
| `unifi://devices` | All devices with formatted summaries |
| `unifi://devices/{site_name}` | Site-specific devices |
| `unifi://device/{mac}` | Single device by MAC address |
| `unifi://clients` | Connected clients with connection details |
| `unifi://clients/{site_name}` | Site-specific clients |
| `unifi://client/{mac}` | Single client by MAC address |
| `unifi://events` | Recent events |
| `unifi://events/{site_name}` | Site-specific events |
| `unifi://alarms` | Active alarms |
| `unifi://alarms/{site_name}` | Site-specific alarms |
| `unifi://health` | Site health status |
| `unifi://health/{site_name}` | Site-specific health |
| `unifi://sites` | All sites |
| `unifi://wlans` | WLAN configurations |
| `unifi://wlans/{site_name}` | Site-specific WLANs |
| `unifi://networks` | Network/VLAN configurations |
| `unifi://networks/{site_name}` | Site-specific networks |
| `unifi://port-forwarding` | Port forwarding rules |
| `unifi://port-forwarding/{site_name}` | Site-specific port forwarding |
| `unifi://firewall-rules` | Firewall rules |
| `unifi://firewall-rules/{site_name}` | Site-specific firewall rules |
| `unifi://firewall-groups` | Firewall groups |
| `unifi://firewall-groups/{site_name}` | Site-specific firewall groups |
| `unifi://dpi` | DPI statistics |
| `unifi://dpi/{site_name}` | Site-specific DPI stats |
| `unifi://rogue-aps` | Rogue access points |
| `unifi://rogue-aps/{site_name}` | Site-specific rogue APs |
| `unifi://speedtest` | Speed test results |
| `unifi://speedtest/{site_name}` | Site-specific speed tests |

## Environment Variables

See [CONFIG](CONFIG.md) for the full reference. Summary:

| Category | Count | Key Variables |
|----------|-------|---------------|
| Controller credentials | 3 required | `UNIFI_URL`, `UNIFI_USERNAME`, `UNIFI_PASSWORD` |
| Controller options | 2 | `UNIFI_IS_UDM_PRO`, `UNIFI_VERIFY_SSL` |
| MCP server | 6 | `UNIFI_MCP_HOST`, `UNIFI_MCP_PORT`, `UNIFI_MCP_TOKEN`, `UNIFI_MCP_TRANSPORT`, `UNIFI_MCP_NO_AUTH`, `UNIFI_MCP_LOG_LEVEL` |
| Safety gates | 2 | `UNIFI_MCP_ALLOW_DESTRUCTIVE`, `UNIFI_MCP_ALLOW_YOLO` |
| Docker | 3 | `PUID`, `PGID`, `DOCKER_NETWORK` |

## Plugin Surfaces

| Surface | File | Description |
|---------|------|-------------|
| Claude Code plugin | `.claude-plugin/plugin.json` | Plugin manifest with userConfig |
| Codex plugin | `.codex-plugin/plugin.json` | Codex manifest with interface metadata |
| Gemini extension | `gemini-extension.json` | Gemini extension with MCP server config |
| MCP Registry | `server.json` | Registry entry for tv.tootie/unifi-mcp |
| Hooks | `hooks/hooks.json` | SessionStart and PostToolUse hooks |
| Skill | `skills/unifi/SKILL.md` | Bundled skill definition |

## Dependencies

### Runtime

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | 2.12.0 | MCP server framework |
| `httpx` | >=0.28.1 | Async HTTP client for UniFi API |
| `python-dotenv` | >=1.1.1 | Environment file loading |
| `fastapi` | >=0.116.1 | ASGI framework (via FastMCP) |
| `uvicorn` | >=0.30.0 | ASGI server |
| `unifi-controller-api` | >=0.3.0 | UniFi API types |

### Development

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.4.1 | Test framework |
| `pytest-asyncio` | >=0.24.0 | Async test support |
| `pytest-cov` | >=6.0.0 | Coverage reporting |
| `inline-snapshot` | >=0.13.0 | Snapshot testing |
| `ruff` | >=0.12.7 | Linting and formatting |
| `ty` | >=0.0.1a6 | Type checking |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/check-docker-security.sh` | Dockerfile security audit |
| `scripts/check-no-baked-env.sh` | Detect baked env vars in Docker |
| `scripts/ensure-ignore-files.sh` | Validate .gitignore/.dockerignore |
| `scripts/check-outdated-deps.sh` | Check for outdated dependencies |
| `scripts/smoke-test.sh` | End-to-end smoke test |
| `hooks/scripts/sync-env.sh` | Sync userConfig to .env |
| `hooks/scripts/fix-env-perms.sh` | Fix .env file permissions |
| `hooks/scripts/ensure-ignore-files.sh` | Ensure ignore file entries |
