# UniFi Local Controller MCP Server

A Model Context Protocol (MCP) server that provides direct integration with local UniFi controllers, built with FastMCP and streamable HTTP transport.

## Overview

This MCP server enables programmatic access to your local UniFi controller through a comprehensive set of tools and resources. Unlike cloud-based solutions, this server connects directly to your UniFi controller for real-time device management and network monitoring.

**Key Features:**
- Direct local controller integration with Cloud Gateway Max and UniFi 7 AP support
- Real-time device status, statistics, and management
- **Clean, formatted output** - No more overwhelming JSON walls, just essential information
- **Smart data formatting** - Human-readable bandwidth, uptimes, and device-specific details
- Comprehensive network configuration access
- Device management operations (restart, locate, client reconnection)
- FastMCP resources with `unifi://` URI scheme for structured data access

## Quick Start

### Prerequisites
- Local UniFi controller (Cloud Gateway Max, UDM Pro, or traditional controller)
- Direct network access to the controller
- Local controller account (not UniFi Cloud/SSO account)
- Python 3.11+
- `uv` package manager

### Controller Compatibility
- **UniFi OS devices** (UDM Pro, UDM SE, Cloud Gateway Max, Cloud Key Gen2+): Uses HTTPS port 443
- **Legacy controllers** (Software controllers, Cloud Key Gen1): Uses HTTPS port 8443
- **Authentication**: Requires local admin account, not UniFi Cloud credentials

### Installation

1. **Clone and setup:**
   ```bash
   cd unifi-mcp
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your controller details
   ```

3. **Run the server:**
   ```bash
   ./run.sh
   # Or directly: uv run python unifi-local-mcp-server.py
   ```

The server runs on `http://localhost:8001/mcp` by default.

## Configuration

### Required Environment Variables

```bash
# Controller connection (scheme and port required)
UNIFI_CONTROLLER_URL=https://10.1.0.1:443  # UniFi OS (UDM Pro, Cloud Gateway Max)
# UNIFI_CONTROLLER_URL=https://10.1.0.1:8443  # Legacy controllers
UNIFI_USERNAME=admin                        # Local controller admin username
UNIFI_PASSWORD=your_password               # Local controller admin password

# Controller type configuration
UNIFI_IS_UDM_PRO=true                 # true for UniFi OS devices, false for legacy
UNIFI_VERIFY_SSL=false                # false for self-signed certs, true for valid SSL

# Optional server settings
UNIFI_LOCAL_MCP_HOST=0.0.0.0          # Server bind address
UNIFI_LOCAL_MCP_PORT=8001             # Server port
UNIFI_LOCAL_MCP_LOG_LEVEL=INFO        # Logging level
```

### Controller URL Examples
- **UniFi OS devices**: `https://192.168.1.1:443` (UDM Pro, Cloud Gateway Max, Cloud Key Gen2+)
- **Legacy controllers**: `https://unifi.example.com:8443` (Software controllers, Cloud Key Gen1)
- **Custom ports**: Include the actual port if different from defaults

### SSL Certificate Handling
- **Self-signed certificates** (common): Set `UNIFI_VERIFY_SSL=false`
- **Valid SSL certificates**: Set `UNIFI_VERIFY_SSL=true`
- **Custom CA bundle**: Provide path to CA bundle file

## Available Tools

### Device Management
- `get_devices` - List all devices with clean, formatted summaries (no raw JSON)
- `get_device_by_mac` - Get specific device details with formatted output
- `restart_device` - Restart a UniFi device
- `locate_device` - Trigger locate LED on device

### Client Management  
- `get_clients` - List connected clients with formatted connection details
- `reconnect_client` - Force client reconnection

### Network Configuration
- `get_sites` - List all controller sites
- `get_wlan_configs` - Wireless network configurations
- `get_network_configs` - Network/VLAN configurations
- `get_port_configs` - Switch port profiles
- `get_port_forwarding_rules` - Port forwarding rules

### Monitoring & Statistics
- `get_controller_status` - Controller system information
- `get_events` - Recent controller events
- `get_alarms` - Active system alarms
- `get_dpi_stats` - Deep Packet Inspection statistics
- `get_rogue_aps` - Detected rogue access points
- `start_spectrum_scan` - Start RF spectrum scan on access point
- `get_spectrum_scan_state` - Get spectrum scan results
- `authorize_guest` - Authorize guest network access

## MCP Resources

Access structured data using the `unifi://` URI scheme:

### Root Level Resources
- `unifi://sites` - All controller sites
- `unifi://devices` - All devices with clean formatting (default site)
- `unifi://clients` - All connected clients with essential details (default site)
- `unifi://dashboard` - Dashboard metrics and time-series data (default site)
- `unifi://overview` - Network overview with glanceable info (default site)
- `unifi://events` - Recent events (default site)
- `unifi://alarms` - Active alarms (default site)
- `unifi://health` - Site health status (default site)
- `unifi://config/networks` - Network configurations (default site)
- `unifi://config/wlans` - WLAN configurations (default site)
- `unifi://config/portforward` - Port forwarding rules (default site)
- `unifi://stats/bandwidth` - Bandwidth statistics (default site)
- `unifi://stats/dpi` - DPI statistics (default site)
- `unifi://channels` - Current wireless channels (default site)
- `unifi://device-tags` - Device tags (default site)
- `unifi://rogue-aps` - Detected rogue access points (default site)
- `unifi://admins` - Administrator accounts
- `unifi://sysinfo` - Controller system information

### Site-Specific Resources
- `unifi://devices/{site_name}` - Devices with clean formatting for specific site
- `unifi://clients/{site_name}` - Clients with essential details for specific site
- `unifi://dashboard/{site_name}` - Dashboard metrics for specific site
- `unifi://overview/{site_name}` - Network overview for specific site
- `unifi://stats/bandwidth/{site_name}` - Bandwidth statistics
- `unifi://stats/dpi/{site_name}` - DPI statistics
- `unifi://config/networks/{site_name}` - Network configurations
- `unifi://config/wlans/{site_name}` - WLAN configurations
- `unifi://config/portforward/{site_name}` - Port forwarding rules
- `unifi://events/{site_name}` - Recent events
- `unifi://alarms/{site_name}` - Active alarms
- `unifi://health/{site_name}` - Site health status
- `unifi://channels/{site_name}` - Current wireless channels
- `unifi://device-tags/{site_name}` - Device tags
- `unifi://rogue-aps/{site_name}` - Detected rogue access points

### Device-Specific Resources
- `unifi://device/{site_name}/{mac}` - Individual device details with clean formatting
- `unifi://stats/device/{site_name}/{mac}` - Device performance stats

### Additional Resources
- `unifi://sites/{site_name}` - Detailed site information including health data

## Architecture

### Core Components

**UnifiControllerClient** - Handles authentication and API communication
- Supports both UDM Pro and legacy controller authentication
- Automatic session management with TOKEN cookies and CSRF tokens
- Comprehensive error handling and retry logic

**FastMCP Integration** - Modern MCP server framework
- Streamable HTTP transport on port 8001
- Structured resource system with URI templates
- Comprehensive tool registration and validation

**Data Formatting** - Clean, comprehensible output
- **Smart Summarization** - Essential information only, no overwhelming JSON walls
- **Device-Type Aware** - Different formatting for Access Points, Gateways, and Switches
- **Connection-Type Aware** - Tailored details for wired vs wireless clients
- Automatic byte conversion (B, KB, MB, GB, TB) with raw value preservation
- Human-readable uptimes, timestamps, and signal strengths
- Recursive formatting for nested data structures

### Authentication Flow
1. Login to controller using username/password
2. Extract TOKEN cookie (UDM Pro) or unifises cookie (legacy)
3. Parse CSRF token from JWT payload for UDM Pro devices
4. Include authentication headers in all subsequent requests

### Key Design Decisions
- **Single-file server**: Complete implementation in one file for simplicity
- **Default site assumption**: Most operations default to "default" site
- **Clean data presentation**: Smart formatting helpers eliminate JSON noise
- **Comprehensive resources**: Dashboard, overview, and detailed monitoring capabilities
- **Resource vs Tool pattern**: Resources for data access, tools for operations

## Development

### Running with Hot Reload
```bash
# Install development dependencies
uv sync --extra dev

# Run with hot reload (if available)
uv run reloaderoo unifi-local-mcp-server.py
```

### Testing Tools
```bash
# List available tools
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# Test a specific tool
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_devices"}}'
```

### Common Endpoints
- Health check: `http://localhost:8001/health`
- MCP endpoint: `http://localhost:8001/mcp`
- Tool execution: `http://localhost:8001/mcp/call`

## Troubleshooting

### Authentication Issues
- **401 Errors**: Check username/password and controller URL
- **MFA Required**: Disable MFA or implement MFA support
- **SSL Errors**: Set `UNIFI_VERIFY_SSL=false` for self-signed certificates

### Controller Type Issues
- **UDM Pro/Cloud Gateway Max**: Set `UNIFI_IS_UDM_PRO=true`
- **Legacy Controllers**: Set `UNIFI_IS_UDM_PRO=false`

### Common Problems
- **Empty DPI Stats**: Ensure DPI is enabled in controller settings
- **No Devices Found**: Verify you have admin access to the controller
- **Connection Timeouts**: Check network connectivity and controller availability

## Technical Details

### Built With
- **[unifi-controller-api](https://github.com/tnware/unifi-controller-api)** - Python library for UniFi controller communication
- **[FastMCP](https://github.com/jlowin/fastmcp)** - Modern Model Context Protocol server framework
- **PyPI Package**: [unifi-controller-api](https://pypi.org/project/unifi-controller-api/)

### Implementation Notes
- **Device model mapping**: Automatically translates device codes (e.g., "U7PG2") to human names (e.g., "UniFi AC Pro AP")
- **Authentication retry**: Automatic retry on authentication failure for network resilience
- **Session management**: Handles TOKEN cookies (UniFi OS) and unifises cookies (legacy) automatically
- **CSRF protection**: Extracts and applies CSRF tokens from JWT payloads for UniFi OS devices

### Network Requirements
- **Direct access**: Server must have direct network connectivity to the UniFi controller
- **Port access**: Ensure the appropriate HTTPS port (443 or 8443) is accessible
- **Account type**: Must use local controller account, not UniFi Cloud/SSO credentials
- **Admin privileges**: Account must have administrative access to the controller

## License

This project is open source. See repository for license details.