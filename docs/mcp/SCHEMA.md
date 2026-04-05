# Tool Schema Documentation

## Overview

Tool schemas define the input validation contract for MCP tools. Schemas are defined in Python using Pydantic models with `Annotated` types and `Field` descriptors, and are exported as JSON Schema by FastMCP for client validation.

## UnifiAction Enum

Defined in `unifi_mcp/models/enums.py`. Contains all 31 action values:

```python
class UnifiAction(str, Enum):
    # Device Management (4)
    GET_DEVICES = "get_devices"
    GET_DEVICE_BY_MAC = "get_device_by_mac"
    RESTART_DEVICE = "restart_device"
    LOCATE_DEVICE = "locate_device"

    # Client Management (7)
    GET_CLIENTS = "get_clients"
    RECONNECT_CLIENT = "reconnect_client"
    BLOCK_CLIENT = "block_client"
    UNBLOCK_CLIENT = "unblock_client"
    FORGET_CLIENT = "forget_client"
    SET_CLIENT_NAME = "set_client_name"
    SET_CLIENT_NOTE = "set_client_note"

    # Network Configuration (8)
    GET_SITES = "get_sites"
    GET_WLAN_CONFIGS = "get_wlan_configs"
    GET_NETWORK_CONFIGS = "get_network_configs"
    GET_PORT_CONFIGS = "get_port_configs"
    GET_PORT_FORWARDING_RULES = "get_port_forwarding_rules"
    GET_FIREWALL_RULES = "get_firewall_rules"
    GET_FIREWALL_GROUPS = "get_firewall_groups"
    GET_STATIC_ROUTES = "get_static_routes"

    # Monitoring and Statistics (10)
    GET_CONTROLLER_STATUS = "get_controller_status"
    GET_EVENTS = "get_events"
    GET_ALARMS = "get_alarms"
    GET_DPI_STATS = "get_dpi_stats"
    GET_ROGUE_APS = "get_rogue_aps"
    START_SPECTRUM_SCAN = "start_spectrum_scan"
    GET_SPECTRUM_SCAN_STATE = "get_spectrum_scan_state"
    AUTHORIZE_GUEST = "authorize_guest"
    GET_SPEEDTEST_RESULTS = "get_speedtest_results"
    GET_IPS_EVENTS = "get_ips_events"

    # Authentication (1)
    GET_USER_INFO = "get_user_info"
```

## Action Category Sets

| Set | Actions | Purpose |
|-----|---------|---------|
| `DEVICE_ACTIONS` | 4 | Routes to DeviceService |
| `CLIENT_ACTIONS` | 7 | Routes to ClientService |
| `NETWORK_ACTIONS` | 8 | Routes to NetworkService |
| `MONITORING_ACTIONS` | 10 | Routes to MonitoringService |
| `AUTH_ACTIONS` | 1 | Handled by UnifiService directly |
| `MAC_REQUIRED_ACTIONS` | 12 | Validates `mac` parameter is present |
| `NO_SITE_ACTIONS` | 3 | get_sites, get_controller_status, get_user_info |
| `DESTRUCTIVE_ACTIONS` | 4 | restart_device, block_client, forget_client, reconnect_client |

## UnifiParams Model

Defined in `unifi_mcp/models/params.py`. Pydantic `BaseModel` with field validators.

### Validators

| Validator | Fields | Rule |
|-----------|--------|------|
| `validate_non_negative` | up_bandwidth, down_bandwidth, quota | Must be >= 0 |
| `validate_limit_positive` | limit | Must be > 0 |
| `validate_minutes_positive` | minutes | Must be > 0 |
| `validate_by_filter_values` | by_filter | Must be "by_app" or "by_cat" |
| `validate_action_requirements` | (model) | Cross-field: MAC required, name/note required |

### Action Defaults

Returned by `get_action_defaults()`:

| Action | Default |
|--------|---------|
| `get_clients` | `connected_only: true` |
| `get_alarms` | `active_only: true` |
| `get_dpi_stats` | `by_filter: "by_app"` |
| `authorize_guest` | `minutes: 480` |
| `get_events` | `limit: 100` |
| `get_rogue_aps` | `limit: 20` |
| `get_speedtest_results` | `limit: 20` |
| `get_ips_events` | `limit: 50` |

## ToolResult Format

All responses use FastMCP's `ToolResult` with:
- `content`: List of `TextContent` blocks (human-readable)
- `structured_content`: Dict with machine-readable data

## See Also

- [TOOLS.md](TOOLS.md) — Tool reference
- [PATTERNS.md](PATTERNS.md) — Code patterns
