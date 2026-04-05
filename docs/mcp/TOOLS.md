# MCP Tools Reference

## Design Philosophy

unifi-mcp exposes exactly two MCP tools:

| Tool | Purpose | Parameters |
|------|---------|------------|
| `unifi` | Primary tool — action-based dispatch to 31 operations | `action`, `site_name`, `mac`, `limit`, `connected_only`, `active_only`, `by_filter`, `name`, `note`, `minutes`, `up_bandwidth`, `down_bandwidth`, `quota`, `confirm` |
| `unifi_help` | Returns markdown reference for all actions | _(none)_ |

This 2-tool pattern keeps the MCP surface small while supporting 31 distinct operations. Clients call `unifi_help` first to discover available actions, then call `unifi` with the appropriate action and parameters.

## Primary Tool: `unifi`

### Input Schema

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | yes | — | Action to perform (see action tables below) |
| `site_name` | string | no | `"default"` | UniFi site name (ignored by get_sites, get_controller_status, get_user_info) |
| `mac` | string | no | — | Device or client MAC address (any format: `aa:bb:cc:dd:ee:ff`, `AA-BB-CC-DD-EE-FF`, `aabb.ccdd.eeff`) |
| `limit` | int | no | varies | Maximum results to return |
| `connected_only` | bool | no | `true` | get_clients: only connected clients |
| `active_only` | bool | no | `true` | get_alarms: only active/unarchived alarms |
| `by_filter` | string | no | `"by_app"` | get_dpi_stats: `"by_app"` or `"by_cat"` |
| `name` | string | no | — | set_client_name: new alias name |
| `note` | string | no | — | set_client_note: note text |
| `minutes` | int | no | `480` | authorize_guest: duration in minutes (8 hours default) |
| `up_bandwidth` | int | no | — | authorize_guest: upload limit in Kbps |
| `down_bandwidth` | int | no | — | authorize_guest: download limit in Kbps |
| `quota` | int | no | — | authorize_guest: data quota in MB |
| `confirm` | bool | no | — | Confirm destructive operations |

### Device Management Actions

| Action | MAC | Description | Example |
|--------|-----|-------------|---------|
| `get_devices` | no | List all devices on a site with status, model, uptime | `{"action": "get_devices"}` |
| `get_device_by_mac` | yes | Get detailed info for a specific device | `{"action": "get_device_by_mac", "mac": "aa:bb:cc:dd:ee:ff"}` |
| `restart_device` | yes | **Destructive** — Restart a device | `{"action": "restart_device", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}` |
| `locate_device` | yes | Activate the locate LED on a device | `{"action": "locate_device", "mac": "aa:bb:cc:dd:ee:ff"}` |

### Client Management Actions

| Action | MAC | Extra Params | Description | Example |
|--------|-----|-------------|-------------|---------|
| `get_clients` | no | `connected_only`, `limit` | List clients with connection type, IP, signal | `{"action": "get_clients"}` |
| `reconnect_client` | yes | — | **Destructive** — Force client reconnection | `{"action": "reconnect_client", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}` |
| `block_client` | yes | — | **Destructive** — Block a client from network access | `{"action": "block_client", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}` |
| `unblock_client` | yes | — | Unblock a previously blocked client | `{"action": "unblock_client", "mac": "aa:bb:cc:dd:ee:ff"}` |
| `forget_client` | yes | — | **Destructive** — Remove all client history (GDPR) | `{"action": "forget_client", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}` |
| `set_client_name` | yes | `name` (required) | Set or update client alias name | `{"action": "set_client_name", "mac": "aa:bb:cc:dd:ee:ff", "name": "Living Room TV"}` |
| `set_client_note` | yes | `note` (required) | Set or update client note | `{"action": "set_client_note", "mac": "aa:bb:cc:dd:ee:ff", "note": "Smart TV"}` |

### Network Configuration Actions

| Action | Description | Example |
|--------|-------------|---------|
| `get_sites` | List all sites (ignores `site_name`) | `{"action": "get_sites"}` |
| `get_wlan_configs` | List WLAN configurations with SSID, security, VLAN | `{"action": "get_wlan_configs"}` |
| `get_network_configs` | List network/VLAN configurations with subnets, DHCP | `{"action": "get_network_configs"}` |
| `get_port_configs` | List switch port profiles with PoE, VLAN, security | `{"action": "get_port_configs"}` |
| `get_port_forwarding_rules` | List port forwarding rules with protocol, ports, destination | `{"action": "get_port_forwarding_rules"}` |
| `get_firewall_rules` | List firewall rules with action, protocol, src/dst | `{"action": "get_firewall_rules"}` |
| `get_firewall_groups` | List firewall groups with members | `{"action": "get_firewall_groups"}` |
| `get_static_routes` | List static routes with destination, gateway | `{"action": "get_static_routes"}` |

### Monitoring and Statistics Actions

| Action | MAC | Extra Params | Description | Example |
|--------|-----|-------------|-------------|---------|
| `get_controller_status` | no | — | Controller version and uptime (ignores `site_name`) | `{"action": "get_controller_status"}` |
| `get_events` | no | `limit` (default: 100) | Recent events with timestamps, types, messages | `{"action": "get_events", "limit": 50}` |
| `get_alarms` | no | `active_only` (default: true) | Alarms with severity, timestamps | `{"action": "get_alarms"}` |
| `get_dpi_stats` | no | `by_filter` (default: "by_app") | Deep Packet Inspection statistics | `{"action": "get_dpi_stats", "by_filter": "by_cat"}` |
| `get_rogue_aps` | no | `limit` (default: 20, max: 50) | Rogue access points sorted by signal strength | `{"action": "get_rogue_aps"}` |
| `start_spectrum_scan` | yes | — | Start RF spectrum scan on an AP | `{"action": "start_spectrum_scan", "mac": "aa:bb:cc:dd:ee:ff"}` |
| `get_spectrum_scan_state` | yes | — | Get spectrum scan results | `{"action": "get_spectrum_scan_state", "mac": "aa:bb:cc:dd:ee:ff"}` |
| `authorize_guest` | yes | `minutes`, `up_bandwidth`, `down_bandwidth`, `quota` | Authorize guest network access | `{"action": "authorize_guest", "mac": "aa:bb:cc:dd:ee:ff", "minutes": 120}` |
| `get_speedtest_results` | no | `limit` (default: 20) | Historical speed test results (last 30 days) | `{"action": "get_speedtest_results"}` |
| `get_ips_events` | no | `limit` (default: 50) | IPS/IDS threat events (last 7 days) | `{"action": "get_ips_events"}` |

### Authentication Actions

| Action | Description | Example |
|--------|-------------|---------|
| `get_user_info` | Get OAuth user info (ignores `site_name`); requires MCP OAuth | `{"action": "get_user_info"}` |

## Destructive Operations

Four actions are destructive: `restart_device`, `reconnect_client`, `block_client`, `forget_client`.

### Confirmation Flow

1. Client calls without confirmation:
   ```json
   {"action": "restart_device", "mac": "aa:bb:cc:dd:ee:ff"}
   ```

2. Server returns confirmation prompt:
   ```json
   {
     "content": [{"type": "text", "text": "'restart_device' is a destructive operation. Pass confirm=true to proceed..."}],
     "structured_content": {"error": "confirmation_required", "action": "restart_device"}
   }
   ```

3. Client re-calls with confirmation:
   ```json
   {"action": "restart_device", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}
   ```

### Environment Variable Bypass

| Variable | Default | Effect |
|----------|---------|--------|
| `UNIFI_MCP_ALLOW_DESTRUCTIVE` | `false` | Auto-confirms all destructive operations |
| `UNIFI_MCP_ALLOW_YOLO` | `false` | Skips elicitation entirely |

Intended for CI/testing only.

## Help Tool: `unifi_help`

Takes no parameters. Returns markdown with all actions, parameters, and descriptions.

```json
// Request
{"name": "unifi_help", "arguments": {}}
```

## Response Format

All responses use `ToolResult` with both human-readable text and structured content:

```json
{
  "content": [
    {"type": "text", "text": "Devices (5 total)\n  Cloud Gateway Max | Online | 192.168.1.1\n  ..."}
  ],
  "structured_content": {
    "success": true,
    "message": "Retrieved 5 devices",
    "data": [{"name": "Cloud Gateway Max", "status": "Online", ...}]
  }
}
```

Text content is formatted as compact, token-efficient summaries. Structured content contains the full data for programmatic access.

### Response Size Cap

Responses exceeding 512 KB are truncated with `... [truncated]` appended.

## Error Responses

```json
{
  "content": [{"type": "text", "text": "Error: Device with MAC aa:bb:cc:dd:ee:ff not found"}],
  "structured_content": {"error": "Device with MAC aa:bb:cc:dd:ee:ff not found"}
}
```

Common errors:
- **Invalid action** — action string not in the UnifiAction enum
- **MAC required** — action requires `mac` but none provided
- **Name/note required** — set_client_name/set_client_note missing required parameter
- **Validation error** — negative bandwidth, zero limit, invalid by_filter value
- **Authentication failure** — controller credentials invalid or expired
- **Confirmation required** — destructive action without `confirm=true`

## MAC Address Handling

MAC addresses are normalized internally to lowercase colon-separated format. All of these inputs are equivalent:

- `AA:BB:CC:DD:EE:FF`
- `aa:bb:cc:dd:ee:ff`
- `AA-BB-CC-DD-EE-FF`
- `aabb.ccdd.eeff`

## See Also

- [SCHEMA.md](SCHEMA.md) — Schema definitions
- [AUTH.md](AUTH.md) — Authentication required before tool calls
- [ENV.md](ENV.md) — Safety gate environment variables
- [RESOURCES.md](RESOURCES.md) — Read-only resource URIs
