"""
Data formatting utilities for UniFi MCP Server.

Provides consistent, human-readable formatting for all UniFi API data,
eliminating overwhelming JSON walls and focusing on essential information.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

# Device model mapping for human-readable names
DEVICE_MODEL_MAP = {
    "U7PG2": "UniFi AC Pro AP",
    "U7P": "UniFi AC Pro AP", 
    "U7LR": "UniFi AC LR AP",
    "U7HD": "UniFi AC HD AP",
    "U6LR": "UniFi 6 LR AP",
    "U6Pro": "UniFi 6 Pro AP",
    "U6E": "UniFi 6 Enterprise AP",
    "U7P6": "UniFi 7 Pro AP",
    "UCGMAX": "Cloud Gateway Max",
    "UDMPRO": "Dream Machine Pro",
    "UDMSE": "Dream Machine SE",
    "USW24": "UniFi 24-Port Switch",
    "USW48": "UniFi 48-Port Switch",
    "USWPRO24": "UniFi Pro 24-Port Switch",
    "USWPRO48": "UniFi Pro 48-Port Switch"
}


def get_tx_power_str(device: Dict[str, Any], radio_index: int) -> str:
    """Get TX power string for a radio, handling Unknown values safely."""
    radio_table = device.get("radio_table", [])
    if len(radio_table) <= radio_index:
        return "Unknown dBm"
    
    tx_power = radio_table[radio_index].get("tx_power")
    if tx_power is None or tx_power == "Unknown" or tx_power == "":
        return "Unknown dBm"
    
    try:
        # Try to format as number if it's numeric
        power_val = float(tx_power)
        return f"{power_val} dBm"
    except (ValueError, TypeError):
        return "Unknown dBm"


def get_temperature_str(temp_value) -> str:
    """Get temperature string, handling Unknown values safely."""
    if temp_value is None or temp_value == "Unknown" or temp_value == "":
        return "Unknown°C"
    
    try:
        temp_val = float(temp_value)
        return f"{temp_val}°C"
    except (ValueError, TypeError):
        return "Unknown°C"


def get_percentage_str(value) -> str:
    """Get percentage string, handling Unknown values safely."""
    if value is None or value == "Unknown" or value == "":
        return "Unknown%"
    
    try:
        percent_val = float(value)
        return f"{percent_val:.1f}%"
    except (ValueError, TypeError):
        return "Unknown%"


def get_power_str(value) -> str:
    """Get power string, handling Unknown values safely."""
    if value is None or value == "Unknown" or value == "":
        return "Unknown W"
    
    try:
        power_val = float(value)
        return f"{power_val:.1f}W"
    except (ValueError, TypeError):
        return "Unknown W"


def get_uplink_speed_str(speedtest_status: Dict[str, Any]) -> str:
    """Get uplink speed string, handling Unknown values safely."""
    try:
        download = speedtest_status.get('xput_download', 0) or 0
        upload = speedtest_status.get('xput_upload', 0) or 0
        return f"{download} Mbps down, {upload} Mbps up"
    except (ValueError, TypeError):
        return "Unknown speed"


def format_bytes(bytes_value: Union[int, float, str, None]) -> str:
    """Convert bytes to human-readable format."""
    if bytes_value is None or bytes_value == "":
        return "0 B"
    
    try:
        bytes_val = float(bytes_value)
    except (ValueError, TypeError):
        return "0 B"
    
    if bytes_val == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    
    while bytes_val >= 1024 and unit_index < len(units) - 1:
        bytes_val /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(bytes_val)} {units[unit_index]}"
    else:
        return f"{bytes_val:.1f} {units[unit_index]}"


def format_uptime(uptime_seconds: Union[int, float, str, None]) -> str:
    """Format uptime seconds into human-readable time."""
    if uptime_seconds is None or uptime_seconds == "":
        return "Unknown"
    
    try:
        uptime = int(float(uptime_seconds))
    except (ValueError, TypeError):
        return "Unknown"
    
    if uptime <= 0:
        return "Less than 1 minute"
    
    days = uptime // 86400
    hours = (uptime % 86400) // 3600
    minutes = (uptime % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return ", ".join(parts) if parts else "Less than 1 minute"


def format_timestamp(timestamp: Union[int, float, str, None]) -> str:
    """Format Unix timestamp to human-readable datetime."""
    if timestamp is None or timestamp == "":
        return "Unknown"
    
    try:
        ts = float(timestamp)
        if ts > 1e10:  # Milliseconds
            ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return "Unknown"


def format_signal_strength(rssi: Union[int, float, str, None]) -> str:
    """Format RSSI signal strength with quality indicator."""
    if rssi is None or rssi == "":
        return "Unknown"
    
    try:
        signal = int(float(rssi))
    except (ValueError, TypeError):
        return "Unknown"
    
    if signal >= -50:
        quality = "Excellent"
    elif signal >= -60:
        quality = "Good"
    elif signal >= -70:
        quality = "Fair"
    else:
        quality = "Poor"
    
    return f"{signal} dBm ({quality})"


def get_device_type_name(device: Dict[str, Any]) -> str:
    """Determine human-readable device type."""
    device_type = device.get("type", "").lower()
    
    if device_type == "uap":
        return "Access Point"
    elif device_type in ["udm", "ugw"]:
        return "Gateway"
    elif device_type == "usw":
        return "Switch"
    elif device_type == "usg":
        return "Security Gateway"
    elif device_type == "uck":
        return "Cloud Key"
    
    return "Unknown Device"


def get_device_model_name(model: str) -> str:
    """Get human-readable device model name."""
    if not model:
        return "Unknown Model"
    
    # Direct mapping
    if model.upper() in DEVICE_MODEL_MAP:
        return DEVICE_MODEL_MAP[model.upper()]
    
    # Fallback patterns
    model_upper = model.upper()
    if "U7" in model_upper and "AP" not in model_upper:
        return f"UniFi {model} AP"
    elif "U6" in model_upper and "AP" not in model_upper:
        return f"UniFi {model} AP"
    elif "USW" in model_upper:
        return f"UniFi {model} Switch"
    elif "UDM" in model_upper:
        return f"Dream Machine {model.replace('UDM', '').strip()}"
    elif "UCG" in model_upper:
        return f"Cloud Gateway {model.replace('UCG', '').strip()}"
    
    return model


def format_device_summary(device: Dict[str, Any]) -> Dict[str, Any]:
    """Format device data into clean, readable summary."""
    device_type = get_device_type_name(device)
    model_name = get_device_model_name(device.get("model", ""))
    
    # Base device info
    summary = {
        "name": device.get("name", "Unnamed Device"),
        "model": model_name,
        "type": device_type,
        "status": "Online" if device.get("state") == 1 else "Offline",
        "uptime": format_uptime(device.get("uptime", 0)),
        "mac": device.get("mac", "").upper(),
        "ip": device.get("ip", "Unknown"),
        "version": device.get("version", "Unknown")
    }
    
    # Add device-specific details
    if device_type == "Access Point":
        summary.update({
            "clients_2g": device.get("num_sta", 0) - device.get("num-sta", 0),
            "clients_5g": device.get("num-sta", 0),
            "total_clients": device.get("num_sta", 0),
            "channel_2g": device.get("radio_table", [{}])[0].get("channel") if device.get("radio_table") else None,
            "channel_5g": device.get("radio_table", [{}])[1].get("channel") if len(device.get("radio_table", [])) > 1 else None,
            "tx_power_2g": get_tx_power_str(device, 0),
            "tx_power_5g": get_tx_power_str(device, 1)
        })
    
    elif device_type == "Gateway":
        summary.update({
            "wan_ip": device.get("wan1", {}).get("ip", "Unknown"),
            "lan_ip": device.get("lan_ip", "Unknown"),
            "uplink_speed": get_uplink_speed_str(device.get('speedtest-status', {})),
            "cpu_usage": get_percentage_str(device.get('system-stats', {}).get('cpu', 0)),
            "memory_usage": get_percentage_str(device.get('system-stats', {}).get('mem', 0)),
            "temperature": get_temperature_str(device.get('general_temperature'))
        })
    
    elif device_type == "Switch":
        port_table = device.get("port_table", [])
        active_ports = len([p for p in port_table if p.get("up", False)])
        poe_power = sum(p.get("poe_power", 0) for p in port_table)
        
        summary.update({
            "total_ports": len(port_table),
            "active_ports": active_ports,
            "poe_power_used": get_power_str(poe_power),
            "cpu_usage": get_percentage_str(device.get('system-stats', {}).get('cpu', 0)),
            "memory_usage": get_percentage_str(device.get('system-stats', {}).get('mem', 0))
        })
    
    return summary


def format_client_summary(client: Dict[str, Any]) -> Dict[str, Any]:
    """Format client data into clean, readable summary."""
    is_wired = client.get("is_wired", False)
    
    summary = {
        "name": client.get("name") or client.get("hostname", "Unknown Device"),
        "mac": client.get("mac", "").upper(),
        "ip": client.get("ip", "Unknown"),
        "connection_type": "Wired" if is_wired else "Wireless",
        "connected_time": format_uptime(client.get("uptime", 0)),
        "last_seen": format_timestamp(client.get("last_seen", 0)),
        "bytes_sent": format_bytes(client.get("tx_bytes", 0)),
        "bytes_received": format_bytes(client.get("rx_bytes", 0)),
        "device_type": client.get("oui", "Unknown Manufacturer")
    }
    
    # Add wireless-specific details
    if not is_wired:
        summary.update({
            "signal_strength": format_signal_strength(client.get("rssi")),
            "access_point": client.get("ap_mac", "Unknown"),
            "frequency": f"{client.get('channel', 'Unknown')} ({client.get('radio', 'Unknown')})",
            "tx_rate": f"{client.get('tx_rate', 0)} Mbps",
            "rx_rate": f"{client.get('rx_rate', 0)} Mbps"
        })
    else:
        summary.update({
            "switch_port": client.get("sw_port", "Unknown"),
            "switch_mac": client.get("sw_mac", "Unknown"),
            "port_speed": f"{client.get('wired-tx_bytes-r', 0) + client.get('wired-rx_bytes-r', 0)} Mbps"
        })
    
    return summary


def format_site_summary(site: Dict[str, Any]) -> Dict[str, Any]:
    """Format site data into clean, readable summary."""
    health = site.get("health", [])
    
    # Calculate overall health score
    total_subsystems = len(health)
    healthy_subsystems = len([h for h in health if h.get("status") == "ok"])
    health_percentage = (healthy_subsystems / total_subsystems * 100) if total_subsystems > 0 else 0
    
    return {
        "name": site.get("desc", site.get("name", "Unknown Site")),
        "site_id": site.get("name", "Unknown"),
        "role": site.get("role", "admin"),
        "health_score": f"{health_percentage:.1f}%",
        "total_devices": sum(site.get("num_" + device_type, 0) for device_type in ["ap", "gw", "sw"]),
        "access_points": site.get("num_ap", 0),
        "gateways": site.get("num_gw", 0),
        "switches": site.get("num_sw", 0),
        "alerts": site.get("num_adopted", 0),
        "health_details": {h.get("subsystem"): h.get("status") for h in health}
    }


def format_device_text(device: Dict[str, Any]) -> str:
    """Format device into clean text representation."""
    name = device.get('name', 'Unknown Device')
    model = device.get('model', 'Unknown Model')
    status = "Online" if device.get('state') == 1 else "Offline"
    uptime = device.get('uptime', 0)
    
    # Format uptime
    if uptime > 0:
        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        if days > 0:
            uptime_str = f"{days}d {hours}h"
        else:
            uptime_str = f"{hours}h"
    else:
        uptime_str = "Unknown"
    
    # Determine device icon
    device_type = device.get('type', '')
    if device_type == 'uap':
        icon = "📡"
    elif device_type == 'ugw':
        icon = "🌐"
    elif device_type == 'usw':
        icon = "🔌"
    else:
        icon = "📱"
    
    return f"{icon} {name} ({model}) - {status}, {uptime_str}"


def format_client_text(client: Dict[str, Any]) -> str:
    """Format client into clean text representation."""
    name = client.get("name") or client.get("hostname", "Unknown Device")
    ip = client.get("ip", "Unknown")
    is_wired = client.get("is_wired", False)
    connection_type = "Wired" if is_wired else "Wireless"
    
    # Connection icon
    icon = "🔌" if is_wired else "📶"
    
    # Signal strength for wireless
    if not is_wired:
        rssi = client.get("rssi")
        if rssi:
            signal = f", {rssi}dBm"
        else:
            signal = ""
    else:
        signal = ""
    
    return f"{icon} {name} ({ip}) - {connection_type}{signal}"


def format_site_text(site: Dict[str, Any]) -> str:
    """Format site into clean text representation."""
    name = site.get("desc", site.get("name", "Unknown Site"))
    site_id = site.get("name", "Unknown")
    role = site.get("role", "admin")
    
    # Calculate health
    health = site.get("health", [])
    total_subsystems = len(health)
    healthy_subsystems = len([h for h in health if h.get("status") == "ok"])
    health_percentage = (healthy_subsystems / total_subsystems * 100) if total_subsystems > 0 else 0
    
    # Device counts - try multiple field name patterns
    aps = site.get("num_ap", site.get("ap_count", site.get("access_points", 0)))
    gws = site.get("num_gw", site.get("gw_count", site.get("gateways", 0)))
    sws = site.get("num_sw", site.get("sw_count", site.get("switches", 0)))
    total_devices = aps + gws + sws
    
    return f"{name} (ID: {site_id}) | Role: {role} | Health: {health_percentage:.1f}% | Devices: {total_devices} (APs: {aps}, GWs: {gws}, SWs: {sws})"


def format_devices_list(devices: List[Dict[str, Any]]) -> str:
    """Format list of devices into clean text."""
    if not devices:
        return "No devices found."
    
    device_texts = []
    for device in devices:
        try:
            device_texts.append(format_device_text(device))
        except Exception:
            name = device.get('name', 'Unknown Device')
            mac = device.get('mac', 'Unknown MAC')
            device_texts.append(f"⚠️ {name} (MAC: {mac}) - Error")
    
    return f"UniFi Network Devices ({len(devices)} total): " + " | ".join(device_texts)


def format_clients_list(clients: List[Dict[str, Any]]) -> str:
    """Format list of clients into clean text."""
    if not clients:
        return "No clients connected."
    
    client_texts = []
    for client in clients:
        try:
            client_texts.append(format_client_text(client))
        except Exception:
            name = client.get('name', 'Unknown Device')
            mac = client.get('mac', 'Unknown MAC')
            client_texts.append(f"⚠️ {name} (MAC: {mac}) - Error")
    
    return f"Connected Clients ({len(clients)} total): " + " | ".join(client_texts)


def format_sites_list(sites: List[Dict[str, Any]]) -> str:
    """Format list of sites into clean text."""
    if not sites:
        return "No sites found."
    
    # For single site (most common), show details
    if len(sites) == 1:
        return f"UniFi Controller Site: {format_site_text(sites[0])}"
    else:
        # Multiple sites
        site_texts = []
        for site in sites:
            try:
                site_texts.append(format_site_text(site))
            except Exception:
                name = site.get("desc", site.get("name", "Unknown"))
                site_texts.append(f"⚠️ {name} - Error")
        
        return f"UniFi Controller Sites ({len(sites)} total): " + " | ".join(site_texts)


def format_network_text(network: Dict[str, Any]) -> str:
    """Format network config into clean text representation."""
    name = network.get("name", "Unknown Network")
    purpose = network.get("purpose", "Unknown")
    vlan = network.get("vlan", "None")
    subnet = network.get("ip_subnet", "Unknown")
    dhcp_enabled = network.get("dhcpd_enabled", False)
    
    # Determine network icon based on purpose
    if purpose == "corporate":
        icon = "🏢"
    elif purpose == "wan":
        icon = "🌍"
    elif purpose == "guest":
        icon = "👥"
    elif purpose == "remote-user-vpn":
        icon = "🔒"
    else:
        icon = "🔗"
    
    parts = [f"{icon} {name}"]
    
    if vlan != "None":
        parts.append(f"VLAN {vlan}")
    if subnet != "Unknown":
        parts.append(subnet)
    if dhcp_enabled:
        parts.append("DHCP")
    
    return " | ".join(parts)


def format_networks_list(networks: List[Dict[str, Any]]) -> str:
    """Format list of networks into clean text."""
    if not networks:
        return "No networks configured."
    
    network_texts = []
    for network in networks:
        try:
            network_texts.append(format_network_text(network))
        except Exception:
            name = network.get('name', 'Unknown Network')
            network_texts.append(f"⚠️ {name} - Error")
    
    return f"Network Configurations ({len(networks)} total): " + " | ".join(network_texts)


# --- Additional token‑efficient formatters for tools ---

def format_port_forwarding_list(rules: List[Dict[str, Any]]) -> str:
    """Format port forwarding rules into a compact list with symbols.

    Example:
    Port Forwarding Rules (4 total)
      ✅ web-https: TCP 443 -> 10.0.0.2:443 (log: ❌)
      ✅ ssh: TCP 2002 -> 10.0.0.5:22 (log: ✅)
    """
    if not rules:
        return "Port Forwarding Rules (0 total)\n  -"

    lines: List[str] = [f"Port Forwarding Rules ({len(rules)} total)"]
    for r in rules:
        enabled = "✅" if r.get("enabled") else "❌"
        proto = (r.get("protocol") or r.get("proto") or "").upper()
        ext = r.get("external_port", r.get("dst_port", "?"))
        ip = r.get("internal_ip", r.get("fwd", "?"))
        port = r.get("internal_port", r.get("fwd_port", "?"))
        log = "✅" if r.get("log") else "❌"
        name = r.get("name", "Unnamed Rule")[:40]
        lines.append(f"  {enabled} {name}: {proto} {ext} -> {ip}:{port} (log: {log})")
    return "\n".join(lines)


def format_firewall_rules_list(rules: List[Dict[str, Any]]) -> str:
    """Format firewall rules compactly with key fields and symbols."""
    if not rules:
        return "Firewall Rules (0 total)\n  -"
    lines: List[str] = [f"Firewall Rules ({len(rules)} total)"]
    # Header
    lines.append(f"  {'En':<2} {'Act':<6} {'Proto':<5} {'Src':<18} {'SPort':<7} {'Dst':<18} {'DPort':<7} {'Log':<3}")
    lines.append(f"  {'-'*2:<2} {'-'*6:<6} {'-'*5:<5} {'-'*18:<18} {'-'*7:<7} {'-'*18:<18} {'-'*7:<7} {'-'*3:<3}")
    for r in rules:
        en = "✓" if r.get("enabled") else "✗"
        act = str(r.get("action", "?")).lower()[:6]
        proto = str(r.get("protocol", r.get("proto", "all")))[:5]
        src = str(r.get("src_address", r.get("src", "any")))[:18]
        sport = str(r.get("src_port", "any"))[:7]
        dst = str(r.get("dst_address", "any"))[:18]
        dport = str(r.get("dst_port", "any"))[:7]
        log = "✓" if r.get("logging") or r.get("log") else "✗"
        lines.append(f"  {en:<2} {act:<6} {proto:<5} {src:<18} {sport:<7} {dst:<18} {dport:<7} {log:<3}")
    return "\n".join(lines)


def format_firewall_groups_list(groups: List[Dict[str, Any]]) -> str:
    """Format firewall groups with counts."""
    if not groups:
        return "Firewall Groups (0 total)\n  -"
    lines: List[str] = [f"Firewall Groups ({len(groups)} total)"]
    lines.append(f"  {'Name':<28} {'Type':<10} {'Members':<7} {'Desc':<24}")
    lines.append(f"  {'-'*28:<28} {'-'*10:<10} {'-'*7:<7} {'-'*24:<24}")
    for g in groups:
        name = str(g.get("name", "Unnamed Group"))[:28]
        gtype = str(g.get("group_type", "unknown"))[:10]
        cnt = int(g.get("member_count", len(g.get("group_members", [])) or 0))
        desc = str(g.get("description", ""))[:24]
        lines.append(f"  {name:<28} {gtype:<10} {cnt:<7} {desc:<24}")
    return "\n".join(lines)


def format_static_routes_list(routes: List[Dict[str, Any]]) -> str:
    """Format static routes compactly."""
    if not routes:
        return "Static Routes (0 total)\n  -"
    lines: List[str] = [f"Static Routes ({len(routes)} total)"]
    lines.append(f"  {'En':<2} {'Destination':<22} {'GW':<16} {'Iface':<8} {'Dist':<4}")
    lines.append(f"  {'-'*2:<2} {'-'*22:<22} {'-'*16:<16} {'-'*8:<8} {'-'*4:<4}")
    for r in routes:
        en = "✓" if r.get("enabled") else "✗"
        dest = str(r.get("destination", r.get("static-route_network", "?")))[:22]
        gw = str(r.get("gateway", r.get("static-route_nexthop", "?")))[:16]
        iface = str(r.get("interface", r.get("static-route_interface", "auto")))[:8]
        dist = str(r.get("distance", r.get("static-route_distance", "-")))[:4]
        lines.append(f"  {en:<2} {dest:<22} {gw:<16} {iface:<8} {dist:<4}")
    return "\n".join(lines)


def format_events_list(events: List[Dict[str, Any]]) -> str:
    """Format controller events with a header and compact lines."""
    if not events:
        return "Controller Events (0)\n  -"
    lines: List[str] = [f"Controller Events ({len(events)} shown)"]
    # Show first 10 for brevity in text; full list remains in structured content
    preview = events[:10]
    for e in preview:
        ts = e.get("timestamp") or e.get("time") or ""
        typ = e.get("type", e.get("key", "?"))
        msg = str(e.get("message", e.get("msg", "")))[:80]
        lines.append(f"  • {ts} | {typ}: {msg}")
    if len(events) > len(preview):
        lines.append(f"  ... and {len(events) - len(preview)} more")
    return "\n".join(lines)


def format_alarms_list(alarms: List[Dict[str, Any]]) -> str:
    """Format alarms with active indicator and summary."""
    if not alarms:
        return "Controller Alarms (0)\n  -"
    lines: List[str] = [f"Controller Alarms ({len(alarms)} shown)"]
    preview = alarms[:10]
    for a in preview:
        act = "⚠️" if not a.get("archived") else "🗂"
        ts = a.get("timestamp", "")
        sev = str(a.get("severity", "")).title()[:10]
        msg = str(a.get("message", "")).strip()[:80]
        lines.append(f"  {act} {ts} | {sev}: {msg}")
    if len(alarms) > len(preview):
        lines.append(f"  ... and {len(alarms) - len(preview)} more")
    return "\n".join(lines)


def format_dpi_stats_list(stats: List[Dict[str, Any]]) -> str:
    """Format DPI stats showing top apps/categories with totals."""
    if not stats:
        return "DPI Statistics (0)\n  -"
    lines: List[str] = [f"DPI Statistics ({len(stats)} items)"]
    header_added = False
    count = 0
    for s in stats:
        summ = s.get("summary", {})
        app = str(summ.get("application", s.get("app", s.get("cat", "Unknown"))))[:22]
        tx = s.get("tx_bytes") or s.get("tx_bytes_raw") or 0
        rx = s.get("rx_bytes") or s.get("rx_bytes_raw") or 0
        # Prefer already formatted values if present
        txf = s.get("tx_bytes") if isinstance(s.get("tx_bytes"), str) else format_bytes(tx)
        rxf = s.get("rx_bytes") if isinstance(s.get("rx_bytes"), str) else format_bytes(rx)
        total = format_bytes((tx or 0) + (rx or 0))
        if not header_added:
            lines.append(f"  {'Application':<22} {'TX':<9} {'RX':<9} {'Total':<9}")
            lines.append(f"  {'-'*22:<22} {'-'*9:<9} {'-'*9:<9} {'-'*9:<9}")
            header_added = True
        lines.append(f"  {app:<22} {txf:<9} {rxf:<9} {total:<9}")
        count += 1
        if count >= 10:
            break
    if len(stats) > count:
        lines.append(f"  ... and {len(stats) - count} more")
    return "\n".join(lines)


def format_rogue_aps_list(aps: List[Dict[str, Any]]) -> str:
    """Format rogue APs with signal and channel."""
    if not aps:
        return "Rogue APs (0)\n  -"
    lines: List[str] = [f"Rogue APs ({len(aps)} shown)"]
    preview = aps[:10]
    for ap in preview:
        ssid = ap.get("ssid", ap.get("essid", "Hidden"))[:24]
        bssid = ap.get("bssid", "?")
        ch = ap.get("channel", "?")
        sig = ap.get("signal_strength", ap.get("rssi", "?"))
        threat = ap.get("threat_level", "?")
        lines.append(f"  • {ssid:<24} ch {ch:<3} RSSI {sig:<6} ({threat}) {bssid}")
    if len(aps) > len(preview):
        lines.append(f"  ... and {len(aps) - len(preview)} more")
    return "\n".join(lines)


def format_speedtests_list(results: List[Dict[str, Any]]) -> str:
    """Format speed tests with concise lines."""
    if not results:
        return "Speed Tests (0)\n  -"
    lines: List[str] = [f"Speed Tests ({len(results)} shown)"]
    preview = results[:10]
    for r in preview:
        ts = r.get("timestamp", "")
        dl = r.get("download_mbps", 0)
        ul = r.get("upload_mbps", 0)
        lat = r.get("latency_ms", r.get("ping_ms", 0))
        lines.append(f"  • {ts} | ↓ {dl} Mbps ↑ {ul} Mbps | {lat} ms")
    if len(results) > len(preview):
        lines.append(f"  ... and {len(results) - len(preview)} more")
    return "\n".join(lines)


def format_ips_events_list(events: List[Dict[str, Any]]) -> str:
    """Format IPS/IDS events compactly."""
    if not events:
        return "IPS Events (0)\n  -"
    lines: List[str] = [f"IPS Events ({len(events)} shown)"]
    preview = events[:10]
    for e in preview:
        ts = e.get("timestamp", "")
        sig = str(e.get("signature", "?"))[:36]
        sev = e.get("severity", "?")
        src = e.get("source_ip", e.get("src_ip", "?"))
        dst = e.get("destination_ip", e.get("dst_ip", "?"))
        lines.append(f"  • {ts} [{sev}] {sig} {src} → {dst}")
    if len(events) > len(preview):
        lines.append(f"  ... and {len(events) - len(preview)} more")
    return "\n".join(lines)


def format_wlan_text(wlan: Dict[str, Any]) -> str:
    """Format WLAN config into clean text representation."""
    name = wlan.get("name", "Unknown WLAN")
    enabled = wlan.get("enabled", False)
    security = wlan.get("security", "Unknown")
    vlan = wlan.get("vlan", "Default")
    guest_access = wlan.get("is_guest", False)
    
    # Status and security icons
    status_icon = "✅" if enabled else "❌"
    sec_icon = "🔒" if security.lower() in ["wpapsk", "wpa2psk", "wpa3psk"] else "🔓"
    
    parts = [f"📶 {name} {status_icon}"]
    parts.append(f"{sec_icon} {security}")
    
    if vlan != "Default":
        parts.append(f"VLAN {vlan}")
    if guest_access:
        parts.append("Guest")
    
    return " | ".join(parts)


def format_wlans_list(wlans: List[Dict[str, Any]]) -> str:
    """Format list of WLANs into clean text."""
    if not wlans:
        return "No WLANs configured."
    
    wlan_texts = []
    for wlan in wlans:
        try:
            wlan_texts.append(format_wlan_text(wlan))
        except Exception:
            name = wlan.get('name', 'Unknown WLAN')
            wlan_texts.append(f"⚠️ {name} - Error")
    
    return f"WLAN Configurations ({len(wlans)} total): " + " | ".join(wlan_texts)


def format_generic_list(items: List[Dict[str, Any]], resource_type: str, key_fields: List[str]) -> str:
    """Generic formatter for any list of items with configurable key fields."""
    if not items:
        return f"No {resource_type.lower()} found."
    
    item_texts = []
    for item in items:
        try:
            # Extract key values from the item
            parts = []
            for field in key_fields:
                value = item.get(field)
                if value is not None and value != "" and value != "Unknown":
                    # Format boolean values
                    if isinstance(value, bool):
                        value = "✅" if value else "❌"
                    # Format numeric values with units if needed
                    elif isinstance(value, (int, float)) and field.endswith(('_bytes', 'bytes')):
                        value = format_bytes(value)
                    elif isinstance(value, (int, float)) and field in ('uptime', 'duration'):
                        value = format_uptime(value)
                    
                    parts.append(str(value))
            
            item_texts.append(" | ".join(parts) if parts else "Unknown Item")
            
        except Exception:
            # Fallback for problematic items
            name = item.get('name', item.get('id', 'Unknown'))
            item_texts.append(f"⚠️ {name} - Error")
    
    return f"{resource_type} ({len(items)} total): " + " | ".join(item_texts)


def format_data_values(data: Any) -> Any:
    """Recursively format data values for human consumption."""
    if isinstance(data, dict):
        formatted = {}
        for key, value in data.items():
            # Handle byte values
            if key.endswith(("_bytes", "-bytes", "bytes")) and isinstance(value, (int, float)):
                formatted[key] = format_bytes(value)
                formatted[f"{key}_raw"] = value
            # Handle timestamp values
            elif key in ("time", "last_seen", "first_see", "blocked_time") and isinstance(value, (int, float)):
                formatted[key] = format_timestamp(value)
                formatted[f"{key}_raw"] = value
            # Handle uptime values
            elif key in ("uptime", "duration") and isinstance(value, (int, float)):
                formatted[key] = format_uptime(value)
                formatted[f"{key}_raw"] = value
            # Recursively format nested data
            else:
                formatted[key] = format_data_values(value)
        return formatted
    
    elif isinstance(data, list):
        return [format_data_values(item) for item in data]
    
    else:
        return data


def format_overview_data(
    devices: List[Dict[str, Any]],
    clients: List[Dict[str, Any]],
    gateway_info: Dict[str, Any],
    port_forwarding: List[Dict[str, Any]],
    speed_tests: List[Dict[str, Any]],
    threats: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Format comprehensive network overview data."""
    
    # Device summary
    device_counts = {"Access Points": 0, "Gateways": 0, "Switches": 0, "Other": 0}
    online_devices = 0
    
    for device in devices:
        device_type = get_device_type_name(device)
        device_counts[device_type] = device_counts.get(device_type, 0) + 1
        if device.get("state") == 1:
            online_devices += 1
    
    # Client summary by connection type
    wired_clients = len([c for c in clients if c.get("is_wired", False)])
    wireless_clients = len(clients) - wired_clients
    
    # Speed test summary
    latest_speed_test = None
    if speed_tests:
        latest_speed_test = max(speed_tests, key=lambda x: x.get("time", 0))
        latest_speed_test = {
            "date": format_timestamp(latest_speed_test.get("time")),
            "download": f"{latest_speed_test.get('xput_download', 0)} Mbps",
            "upload": f"{latest_speed_test.get('xput_upload', 0)} Mbps",
            "latency": f"{latest_speed_test.get('latency', 0)} ms"
        }
    
    # Recent threats summary
    recent_threats = len([t for t in threats if t.get("time", 0) > (datetime.now().timestamp() - 86400)])
    
    return {
        "network_summary": {
            "total_devices": len(devices),
            "online_devices": online_devices,
            "device_breakdown": device_counts,
            "total_clients": len(clients),
            "wired_clients": wired_clients,
            "wireless_clients": wireless_clients
        },
        "gateway_info": gateway_info,
        "port_forwarding_rules": len(port_forwarding),
        "latest_speed_test": latest_speed_test,
        "security": {
            "threats_last_24h": recent_threats,
            "total_threat_events": len(threats)
        }
    }
