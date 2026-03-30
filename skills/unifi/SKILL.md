---
name: unifi
description: This skill should be used when the user says "check network", "who's connected", "UniFi devices", "block client", "unblock client", "network health", "firewall rules", "wifi config", "port forwarding", "network stats", "UniFi controller", "connected clients", "network devices", "restart access point", "check alarms", "network events", "DPI stats", "rogue APs", "speedtest results", or mentions UniFi, network monitoring, or client management.
---

# UniFi Skill

## Mode Detection

**MCP mode** (preferred): Use when `mcp__unifi-mcp__*` tools are available. The server handles UniFi controller authentication internally — session cookies are managed server-side.

**HTTP fallback mode**: UniFi requires session-based authentication (login → cookie → requests). This is complex to replicate in curl. **Strongly prefer keeping the MCP server running.** For emergencies only, see fallback section below.

**MCP URL**: `${user_config.unifi_mcp_url}`

---

## MCP Mode — Tool Reference

### Clients

```
mcp__unifi-mcp__get_clients
  connected_only  (optional) true/false — default true (connected only)
  site_name       (optional) default "default"

mcp__unifi-mcp__block_client
  mac        (required) Client MAC address — DESTRUCTIVE, confirm before use
  site_name  (optional) default "default"

mcp__unifi-mcp__unblock_client
  mac        (required) Client MAC address
  site_name  (optional) default "default"

mcp__unifi-mcp__reconnect_client
  mac        (required) Client MAC address
  site_name  (optional) default "default"

mcp__unifi-mcp__forget_client
  mac        (required) Client MAC address — DESTRUCTIVE, removes from history
  site_name  (optional) default "default"

mcp__unifi-mcp__set_client_name
  mac   (required) Client MAC address
  name  (required) New display name
  site_name  (optional) default "default"

mcp__unifi-mcp__set_client_note
  mac   (required) Client MAC address
  note  (required) Note text
  site_name  (optional) default "default"
```

### Devices

```
mcp__unifi-mcp__get_devices
  site_name  (optional) default "default"

mcp__unifi-mcp__get_device_by_mac
  mac        (required) Device MAC address
  site_name  (optional) default "default"

mcp__unifi-mcp__restart_device
  mac        (required) Device MAC address — DESTRUCTIVE, causes brief outage
  site_name  (optional) default "default"

mcp__unifi-mcp__locate_device
  mac        (required) Device MAC address — flashes LED for identification
  site_name  (optional) default "default"
```

### Network

```
mcp__unifi-mcp__get_sites
  (no parameters)

mcp__unifi-mcp__get_wlan_configs
  site_name  (optional) default "default"

mcp__unifi-mcp__get_network_configs
  site_name  (optional) default "default"

mcp__unifi-mcp__get_port_configs
  site_name  (optional) default "default"

mcp__unifi-mcp__get_port_forwarding_rules
  site_name  (optional) default "default"

mcp__unifi-mcp__get_firewall_rules
  site_name  (optional) default "default"

mcp__unifi-mcp__get_firewall_groups
  site_name  (optional) default "default"

mcp__unifi-mcp__get_static_routes
  site_name  (optional) default "default"
```

### Monitoring

```
mcp__unifi-mcp__get_controller_status
  (no parameters)

mcp__unifi-mcp__get_events
  limit      (optional) default 100
  site_name  (optional) default "default"

mcp__unifi-mcp__get_alarms
  active_only  (optional) default true
  site_name    (optional) default "default"

mcp__unifi-mcp__get_dpi_stats
  by_filter  (optional) "by_app" or "by_cat" — default "by_app"
  site_name  (optional) default "default"

mcp__unifi-mcp__get_rogue_aps
  site_name  (optional) default "default"
  limit      (optional) default 20

mcp__unifi-mcp__get_speedtest_results
  site_name  (optional) default "default"
  limit      (optional) default 20

mcp__unifi-mcp__start_spectrum_scan
  mac        (required) Access point MAC address — long-running operation
  site_name  (optional) default "default"

mcp__unifi-mcp__get_spectrum_scan_state
  mac        (required) Access point MAC address
  site_name  (optional) default "default"

mcp__unifi-mcp__authorize_guest
  mac        (required) Guest client MAC address
  site_name  (optional) default "default"
```

---

## Destructive Operations — Confirmation Required

Always confirm with the user before executing:
- `block_client` — blocks network access for a device
- `forget_client` — removes client from controller history
- `restart_device` — reboots an AP or switch, causes brief outage

---

## HTTP Fallback Mode

UniFi uses session-based auth. For emergency fallback:

```bash
# Step 1: Login and capture cookie
COOKIE_JAR=$(mktemp)
curl -s -X POST "$CLAUDE_PLUGIN_OPTION_UNIFI_CONTROLLER_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -k --cookie-jar "$COOKIE_JAR" \
  -d "{\"username\":\"$CLAUDE_PLUGIN_OPTION_UNIFI_USERNAME\",\"password\":\"$CLAUDE_PLUGIN_OPTION_UNIFI_PASSWORD\"}"

# Step 2: Use session for requests
curl -s "$CLAUDE_PLUGIN_OPTION_UNIFI_CONTROLLER_URL/proxy/network/api/s/default/stat/sta" \
  -k --cookie "$COOKIE_JAR"
```

Retrieve credentials:
```bash
echo "$CLAUDE_PLUGIN_OPTION_UNIFI_PASSWORD"
```

---

## Notes

- `site_name` defaults to `"default"` for most single-site deployments
- `start_spectrum_scan` is long-running — poll `get_spectrum_scan_state` for results
- Controller URL typically ends in `:443` for UDM Pro / Cloud Key Gen2+
- SSL verification is usually disabled for self-signed controller certs (handled server-side)
