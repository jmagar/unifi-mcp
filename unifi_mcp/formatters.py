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
            "tx_power_2g": f"{device.get('radio_table', [{}])[0].get('tx_power', 'Unknown')} dBm" if device.get("radio_table") else "Unknown",
            "tx_power_5g": f"{device.get('radio_table', [{}])[1].get('tx_power', 'Unknown')} dBm" if len(device.get("radio_table", [])) > 1 else "Unknown"
        })
    
    elif device_type == "Gateway":
        summary.update({
            "wan_ip": device.get("wan1", {}).get("ip", "Unknown"),
            "lan_ip": device.get("lan_ip", "Unknown"),
            "uplink_speed": f"{device.get('speedtest-status', {}).get('xput_download', 0)} Mbps down, {device.get('speedtest-status', {}).get('xput_upload', 0)} Mbps up",
            "cpu_usage": f"{device.get('system-stats', {}).get('cpu', 0):.1f}%",
            "memory_usage": f"{device.get('system-stats', {}).get('mem', 0):.1f}%",
            "temperature": f"{device.get('general_temperature', 'Unknown')}°C"
        })
    
    elif device_type == "Switch":
        port_table = device.get("port_table", [])
        active_ports = len([p for p in port_table if p.get("up", False)])
        poe_power = sum(p.get("poe_power", 0) for p in port_table)
        
        summary.update({
            "total_ports": len(port_table),
            "active_ports": active_ports,
            "poe_power_used": f"{poe_power:.1f}W",
            "cpu_usage": f"{device.get('system-stats', {}).get('cpu', 0):.1f}%",
            "memory_usage": f"{device.get('system-stats', {}).get('mem', 0):.1f}%"
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