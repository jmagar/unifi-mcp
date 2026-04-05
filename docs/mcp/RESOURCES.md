# MCP Resources Reference

## Overview

MCP resources provide read-only data access via the `unifi://` URI scheme. Resources are registered at server startup and return structured data for LLM consumption.

All resources support an optional `{site_name}` path segment. When omitted, the default site is used.

## Resource Modules

Resources are organized into six modules:

| Module | Resources | Description |
|--------|-----------|-------------|
| `overview_resources` | overview, dashboard | Aggregated network summaries |
| `device_resources` | devices, device/{mac} | Device inventory and details |
| `client_resources` | clients, client/{mac} | Connected client data |
| `monitoring_resources` | events, alarms, health, dpi, rogue-aps, speedtest, firewall-rules, firewall-groups | Monitoring and security |
| `network_resources` | wlans, networks, port-forwarding | Network configuration |
| `site_resources` | sites | Multi-site management |

## Overview Resources

### `unifi://overview`

Network overview with device counts, client counts, gateway info, and port forwarding summary.

```json
{
  "summary": {
    "total_devices": 5,
    "online_devices": 5,
    "device_types": {"Gateway": 1, "Access Point": 2, "Switch": 2, "Other": 0},
    "total_clients": 42,
    "wireless_clients": 30,
    "wired_clients": 12
  },
  "gateway": {
    "name": "Cloud Gateway Max",
    "model": "UCGMAX",
    "wan_ip": "203.0.113.1",
    "lan_ip": "192.168.1.1",
    "uptime": 1234567,
    "version": "4.0.6"
  },
  "port_forwarding": {"total_rules": 8, "enabled_rules": 6}
}
```

### `unifi://dashboard`

Dashboard metrics with WAN/WLAN traffic rates and latency.

```json
{
  "wan_tx_rate": 123456,
  "wan_rx_rate": 789012,
  "wlan_tx_rate": 45678,
  "wlan_rx_rate": 90123,
  "latency_avg": 12.5,
  "timestamp": 1712188800,
  "data_points": 1
}
```

## Device Resources

### `unifi://devices`

All devices with formatted summaries including name, model, status, IP, uptime, firmware version.

### `unifi://device/{mac}`

Single device details by MAC address.

## Client Resources

### `unifi://clients`

Connected clients with name, MAC, IP, connection type (wired/wireless), signal strength, bandwidth usage.

### `unifi://client/{mac}`

Single client details by MAC address.

## Monitoring Resources

### `unifi://events`

Recent controller events (connects, disconnects, roams).

### `unifi://alarms`

Active alarms with severity, timestamps, device associations.

### `unifi://health`

Site health status showing subsystem health (WAN, LAN, WLAN).

### `unifi://dpi`

DPI statistics with application/category traffic volumes.

### `unifi://rogue-aps`

Detected rogue access points with SSID, signal strength, threat level.

### `unifi://speedtest`

Historical speed test results with download/upload speeds, latency.

### `unifi://firewall-rules`

Firewall rules with action, protocol, source/destination.

### `unifi://firewall-groups`

Firewall groups with member lists.

## Network Resources

### `unifi://wlans`

WLAN configurations with SSID, security mode, VLAN, guest access settings.

### `unifi://networks`

Network/VLAN configurations with subnets, DHCP settings.

### `unifi://port-forwarding`

Port forwarding rules with protocol, ports, destination IPs.

## Site Resources

### `unifi://sites`

All sites with name, description, and health summary.

## Site-Specific Variants

All resources (except `unifi://sites`) support a site suffix:

```
unifi://devices/{site_name}
unifi://clients/{site_name}
unifi://events/{site_name}
unifi://dashboard/{site_name}
unifi://overview/{site_name}
```

When no site is specified, `"default"` is used.

## See Also

- [TOOLS.md](TOOLS.md) — Active operations via the `unifi` tool
- [INVENTORY](../INVENTORY.md) — Full component listing
