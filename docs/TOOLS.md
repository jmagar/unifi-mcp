# UniFi MCP Server - Complete Tools Reference

This document provides a comprehensive list of all 29 tools available in the UniFi MCP server, organized by category with detailed descriptions and expected outputs.

## =ñ Device Management Tools (4)

### `get_devices`
- **Description:** List all UniFi devices with essential information
- **Parameters:** `site_name` (default: "default")
- **Output:** Clean device summaries with status, IP, model, uptime
- **Use Case:** Device inventory and status monitoring

### `get_device_by_mac`
- **Description:** Get detailed information for a specific device
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Detailed device info with statistics and configuration
- **Use Case:** Device troubleshooting and detailed inspection

### `restart_device`
- **Description:** Restart a UniFi device remotely
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status of restart command
- **Use Case:** Remote device troubleshooting and maintenance

### `locate_device`
- **Description:** Trigger the locate LED on a UniFi device
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status of locate command
- **Use Case:** Physical device identification in rack/deployment

## =e Client Management Tools (7)

### `get_clients`
- **Description:** Get connected clients with connection details
- **Parameters:** `connected_only` (default: true), `site_name` (default: "default")
- **Output:** Essential client connection information
- **Use Case:** Network client monitoring and analysis

### `reconnect_client`
- **Description:** Force reconnection of a client device
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status of reconnect command
- **Use Case:** Client connectivity troubleshooting

### `block_client`
- **Description:** Block a client from accessing the network
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status with confirmation message
- **Use Case:** Security enforcement, incident response, parental controls

### `unblock_client`
- **Description:** Restore network access for a blocked client
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status with confirmation message
- **Use Case:** Access restoration after security review

### `forget_client`
- **Description:** Remove client historical data (GDPR compliance)
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status of data removal
- **Use Case:** Privacy compliance, database cleanup

### `set_client_name`
- **Description:** Set or update the name/alias for a client
- **Parameters:** `mac` (required), `name` (required), `site_name` (default: "default")
- **Output:** Success/error status with updated name
- **Use Case:** Device identification and network documentation

### `set_client_note`
- **Description:** Add or update notes for a client record
- **Parameters:** `mac` (required), `note` (required), `site_name` (default: "default")
- **Output:** Success/error status with updated note
- **Use Case:** Network documentation and client management

## < Network Configuration Tools (8)

### `get_sites`
- **Description:** Get all controller sites with health information
- **Parameters:** None
- **Output:** Site summaries with health and device counts
- **Use Case:** Multi-site network management

### `get_wlan_configs`
- **Description:** Get wireless network configurations
- **Parameters:** `site_name` (default: "default")
- **Output:** WiFi network settings and security configurations
- **Use Case:** Wireless network management and security audit

### `get_network_configs`
- **Description:** Get network/VLAN configurations
- **Parameters:** `site_name` (default: "default")
- **Output:** Network topology and VLAN settings
- **Use Case:** Network architecture analysis and VLAN management

### `get_port_configs`
- **Description:** Get switch port profile configurations
- **Parameters:** `site_name` (default: "default")
- **Output:** Port profile settings and configurations
- **Use Case:** Switch management and port configuration

### `get_port_forwarding_rules`
- **Description:** Get port forwarding rules
- **Parameters:** `site_name` (default: "default")
- **Output:** Traffic routing rules and port mappings
- **Use Case:** Network services configuration and troubleshooting

### `get_firewall_rules`
- **Description:** Get firewall security rules
- **Parameters:** `site_name` (default: "default")
- **Output:** Firewall rules with actions, sources, and destinations
- **Use Case:** Security audit and firewall management

### `get_firewall_groups`
- **Description:** Get firewall address groups
- **Parameters:** `site_name` (default: "default")
- **Output:** Firewall groups with member addresses
- **Use Case:** Security group management and policy organization

### `get_static_routes`
- **Description:** Get advanced routing configuration
- **Parameters:** `site_name` (default: "default")
- **Output:** Static routes with destinations and gateways
- **Use Case:** Advanced network routing analysis and troubleshooting

## =Ê Monitoring & Statistics Tools (10)

### `get_controller_status`
- **Description:** Get controller system information and status
- **Parameters:** None
- **Output:** Controller health and system information
- **Use Case:** System health monitoring and diagnostics

### `get_events`
- **Description:** Get recent controller events
- **Parameters:** `limit` (default: 100), `site_name` (default: "default")
- **Output:** Event timeline with timestamps and descriptions
- **Use Case:** System monitoring and troubleshooting

### `get_alarms`
- **Description:** Get active system alarms
- **Parameters:** `active_only` (default: true), `site_name` (default: "default")
- **Output:** Alert notifications with severity and details
- **Use Case:** Proactive issue identification and alerting

### `get_dpi_stats`
- **Description:** Get Deep Packet Inspection statistics
- **Parameters:** `by_filter` (default: "by_app"), `site_name` (default: "default")
- **Output:** Traffic analysis by application or category
- **Use Case:** Bandwidth analysis and application monitoring

### `get_rogue_aps`
- **Description:** Get detected rogue access points
- **Parameters:** `site_name` (default: "default"), `limit` (default: 20)
- **Output:** Security threats with signal strength and details
- **Use Case:** Wireless security monitoring and threat detection

### `start_spectrum_scan`
- **Description:** Start RF spectrum analysis on an access point
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** Success/error status of scan initiation
- **Use Case:** Wireless diagnostics and interference analysis

### `get_spectrum_scan_state`
- **Description:** Get RF spectrum scan results
- **Parameters:** `mac` (required), `site_name` (default: "default")
- **Output:** RF environment data and scan results
- **Use Case:** Wireless optimization and interference troubleshooting

### `authorize_guest`
- **Description:** Authorize guest client for network access
- **Parameters:** `mac` (required), `minutes` (default: 480), `up_bandwidth`, `down_bandwidth`, `quota`, `site_name` (default: "default")
- **Output:** Success/error status of guest authorization
- **Use Case:** Guest network management and access control

### `get_speedtest_results`
- **Description:** Get historical internet speed test data
- **Parameters:** `site_name` (default: "default"), `limit` (default: 20)
- **Output:** Speed test results with download/upload speeds and latency
- **Use Case:** ISP performance monitoring and troubleshooting

### `get_ips_events`
- **Description:** Get IPS/IDS security threat detection events
- **Parameters:** `site_name` (default: "default"), `limit` (default: 50)
- **Output:** Security events with threat details and source/destination IPs
- **Use Case:** Security monitoring and threat analysis

---

## Tool Testing Matrix

| Category | Tool Count | Status |
|----------|------------|--------|
| Device Management | 4 | ó Pending |
| Client Management | 7 | ó Pending |
| Network Configuration | 8 | ó Pending |
| Monitoring & Statistics | 10 | ó Pending |
| **Total** | **29** | **ó Pending** |

## Testing Notes

- All tools support the `site_name` parameter with "default" as the standard fallback
- MAC address parameters accept any format (colon, dash, or dot separated) 
- Tools return clean, formatted JSON output with essential information only
- Error handling provides descriptive messages for troubleshooting
- All client management tools include automatic MAC address normalization

## API Compliance

All tools use documented UniFi Controller API endpoints and follow established patterns:
- Authentication via session cookies and CSRF tokens
- Consistent error handling and response formatting
- Site-specific operations with proper parameter validation
- Support for both UDM Pro and traditional UniFi controllers