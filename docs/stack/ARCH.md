# Architecture Overview

MCP server architecture for unifi-mcp.

## Request Flow

```
MCP Client (Claude Code / Desktop / Codex)
  |
  | JSON-RPC over HTTP or stdio
  v
Starlette App (server.py)
  |
  | BearerAuthMiddleware (validates UNIFI_MCP_TOKEN)
  v
FastMCP Router
  |
  | Tool: "unifi" or "unifi_help"
  v
UniFiMCPServer._register_unified_tool()
  |
  | Parse action, validate params (Pydantic)
  | Check destructive gate
  v
UnifiService.execute_action()
  |
  | Route by action category
  v
Domain Service (Device / Client / Network / Monitoring)
  |
  | Format response
  v
UnifiControllerClient
  |
  | httpx async HTTP
  | Session cookies + CSRF token
  v
UniFi Controller API
```

## Component Architecture

### Server Layer

`UniFiMCPServer` (server.py):
- Initializes FastMCP with tool and resource registration
- Wraps FastMCP's HTTP app in Starlette for /health endpoint and bearer auth
- Manages server lifecycle (initialize, run, cleanup)

### Tool Layer

Two registered tools:
- `unifi` — unified action dispatcher with Pydantic validation
- `unifi_help` — static help text

The `unifi` tool validates input via `UnifiParams`, checks the destructive gate, then delegates to `UnifiService`.

### Service Layer

`UnifiService` routes actions to domain services:

| Service | Actions | Module |
|---------|---------|--------|
| `DeviceService` | 4 device actions | `services/device_service.py` |
| `ClientService` | 7 client actions | `services/client_service.py` |
| `NetworkService` | 8 network actions | `services/network_service.py` |
| `MonitoringService` | 10 monitoring actions | `services/monitoring_service.py` |
| `UnifiService` | 1 auth action | `services/unifi_service.py` |

All services extend `BaseService` which provides:
- MAC normalization
- Error/success result construction
- Response validation
- List response checking

### Client Layer

`UnifiControllerClient` (client.py):
- Async HTTP client using httpx
- Session-based authentication (UDM Pro JWT or legacy cookie)
- Auto-reauthentication on 401
- CSRF token management
- Both raw API methods and formatted/summary methods

### Resource Layer

Six resource modules register `unifi://` URIs:
- Overview: aggregated dashboard and network overview
- Devices: device inventory
- Clients: connected client data
- Monitoring: events, alarms, health, DPI, rogue APs, speedtest, firewall
- Networks: WLAN, VLAN, port forwarding
- Sites: multi-site management

### Formatter Layer

`formatters.py` converts raw UniFi API data to:
- Human-readable device/client/site summaries
- Compact list formats for token efficiency
- Formatted byte values (KB, MB, GB)
- Timestamp conversion

## Data Flow

```
UniFi API Response (raw JSON)
  -> dict_items() filter (keep only dict entries)
  -> format_*_summary() per item
  -> format_*_list() for compact text
  -> ToolResult(content=[text], structured_content=data)
  -> _truncate_response() if > 512 KB
  -> MCP Client
```

## See Also

- [TECH.md](TECH.md) — Technology choices
- [PATTERNS](../mcp/PATTERNS.md) — Code patterns
