"""
Device-related MCP resources for UniFi MCP Server.

Provides structured access to device information and statistics.
"""

import json
import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_data_values

logger = logging.getLogger(__name__)


def filter_device_data(devices):
    """Filter device data to show only essential information."""
    filtered_devices = []
    
    for device in devices:
        # Extract essential device info
        filtered_device = {
            "name": device.get("name", "Unknown Device"),
            "mac": device.get("mac", "Unknown"),
            "model": device.get("model", "Unknown"),
            "type": get_device_type_name(device),
            "status": "Online" if device.get("state", 0) == 1 else "Offline",
            "ip": device.get("ip", "Unknown"),
            "uptime": format_uptime(device.get("uptime", 0)),
            "version": device.get("version", "Unknown")
        }
        
        # Add device-type specific info
        device_type = device.get('type', '')
        if device_type == 'uap':  # Access Point
            filtered_device["clients"] = device.get('num_sta', 0)
            # Add basic radio info
            radio_table = device.get("radio_table", [])
            if radio_table:
                filtered_device["radios"] = len(radio_table)
        elif device_type == 'usw':  # Switch
            port_table = device.get('port_table', [])
            active_ports = len([p for p in port_table if p.get('up', False)])
            filtered_device["ports"] = f"{active_ports}/{len(port_table)}"
        elif device_type == 'ugw':  # Gateway
            wan_info = device.get('wan1', {})
            if wan_info:
                filtered_device["wan_ip"] = wan_info.get('ip', 'Unknown')
        
        filtered_devices.append(filtered_device)
    
    return filtered_devices

def get_device_type_name(device):
    """Get human-readable device type name."""
    device_type = device.get('type', '')
    if device_type == 'uap':
        return "Access Point"
    elif device_type == 'ugw':
        return "Gateway"
    elif device_type == 'usw':
        return "Switch"
    else:
        return "Device"

def format_uptime(uptime):
    """Format uptime in human readable format."""
    if isinstance(uptime, (int, float)) and uptime > 0:
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        if days > 0:
            return f"{days}d {hours}h"
        else:
            return f"{hours}h"
    return "Unknown"

def register_device_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all device-related MCP resources."""
    
    @mcp.resource("unifi://devices")
    async def resource_all_devices():
        """Get all devices with clean formatting (default site)."""
        try:
            devices = await client.get_devices("default")
            
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices: {devices['error']}"
            
            if not isinstance(devices, list):
                return "Error: Unexpected response format"
            
            filtered_devices = filter_device_data(devices)
            return json.dumps(filtered_devices, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"Error retrieving devices: {str(e)}"
    
    
    @mcp.resource("unifi://devices/{site_name}")
    async def resource_site_devices(site_name: str):
        """Get all devices with clean formatting for specific site."""
        try:
            devices = await client.get_devices(site_name)
            
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices for site {site_name}: {devices['error']}"
            
            if not isinstance(devices, list):
                return "Error: Unexpected response format"
            
            filtered_devices = filter_device_data(devices)
            return filtered_devices
            
        except Exception as e:
            return f"Error retrieving devices for site {site_name}: {str(e)}"
    
    @mcp.resource("unifi://device/{site_name}/{mac}")
    async def resource_device_detail(site_name: str, mac: str):
        """Get individual device details with clean formatting."""
        try:
            devices = await client.get_devices(site_name)
            
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices for site {site_name}: {devices['error']}"
            
            if not isinstance(devices, list):
                return "Error: Unexpected response format"
            
            # Normalize MAC address for comparison
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # Find matching device
            for device in devices:
                device_mac = device.get("mac", "").lower().replace("-", ":").replace(".", ":")
                if device_mac == normalized_mac:
                    filtered_device = filter_device_data([device])[0]
                    return filtered_device
            
            return f"Device with MAC address {mac} not found in site {site_name}"
            
        except Exception as e:
            logger.error(f"Error in device detail resource for {mac}: {e}")
            return f"Error retrieving device details for {mac}: {str(e)}"
    
    
    @mcp.resource("unifi://stats/device/{site_name}/{mac}")
    async def resource_device_stats(site_name: str, mac: str):
        """Get device performance statistics with clean formatting."""
        try:
            devices = await client.get_devices(site_name)
            
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices for site {site_name}: {devices['error']}"
            
            if not isinstance(devices, list):
                return "Error: Unexpected response format"
            
            # Normalize MAC address for comparison
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # Find matching device
            for device in devices:
                device_mac = device.get("mac", "").lower().replace("-", ":").replace(".", ":")
                if device_mac == normalized_mac:
                    name = device.get("name", "Unknown")
                    model = device.get("model", "Unknown")
                    uptime = device.get("uptime", 0)
                    
                    # Format uptime
                    if isinstance(uptime, (int, float)):
                        days = int(uptime // 86400)
                        hours = int((uptime % 86400) // 3600)
                        uptime_str = f"{days}d {hours}h"
                    else:
                        uptime_str = "Unknown"
                    
                    summary = "**Device Performance Statistics**\n\n"
                    summary += f"**📊 {name}** ({model})\n"
                    summary += f"  • MAC: {device.get('mac', '').upper()}\n"
                    summary += f"  • Uptime: {uptime_str}\n\n"
                    
                    # Traffic statistics
                    tx_bytes = device.get("tx_bytes", 0)
                    rx_bytes = device.get("rx_bytes", 0)
                    tx_packets = device.get("tx_packets", 0)
                    rx_packets = device.get("rx_packets", 0)
                    tx_dropped = device.get("tx_dropped", 0)
                    rx_dropped = device.get("rx_dropped", 0)
                    
                    if tx_bytes > 0 or rx_bytes > 0:
                        formatted_traffic = format_data_values({
                            "tx_bytes": tx_bytes,
                            "rx_bytes": rx_bytes,
                            "total_bytes": tx_bytes + rx_bytes
                        })
                        
                        summary += "📦 **Traffic Statistics**\n"
                        summary += f"  • Total Data: {formatted_traffic.get('total_bytes', '0 B')}\n"
                        summary += f"  • Transmitted: {formatted_traffic.get('tx_bytes', '0 B')} ({tx_packets:,} packets)\n"
                        summary += f"  • Received: {formatted_traffic.get('rx_bytes', '0 B')} ({rx_packets:,} packets)\n"
                        if tx_dropped > 0 or rx_dropped > 0:
                            summary += f"  • Dropped: TX {tx_dropped:,}, RX {rx_dropped:,}\n"
                        summary += "\n"
                    
                    # System stats (for gateways/switches)
                    system_stats = device.get("system-stats", {})
                    if system_stats:
                        cpu = system_stats.get("cpu", "Unknown")
                        mem = system_stats.get("mem", "Unknown")
                        
                        summary += "🖥️ **System Performance**\n"
                        if cpu != "Unknown":
                            summary += f"  • CPU Usage: {cpu}%\n"
                        if mem != "Unknown":
                            summary += f"  • Memory Usage: {mem}%\n"
                        summary += "\n"
                    
                    # Radio stats (for access points)
                    radio_table = device.get("radio_table", [])
                    if radio_table:
                        summary += "📶 **Radio Statistics**\n"
                        for i, radio in enumerate(radio_table[:2]):  # Limit to 2 radios
                            radio_name = radio.get("name", f"Radio {i+1}")
                            channel = radio.get("channel", "Unknown")
                            tx_power = radio.get("tx_power", "Unknown")
                            num_clients = radio.get("num_sta", 0)
                            
                            summary += f"  • {radio_name}: Ch {channel}, {tx_power}dBm, {num_clients} clients\n"
                        summary += "\n"
                    
                    # Port stats (for switches)
                    port_table = device.get("port_table", [])
                    if port_table:
                        active_ports = [p for p in port_table if p.get("up", False)]
                        summary += "🔌 **Port Statistics**\n"
                        summary += f"  • Total Ports: {len(port_table)}\n"
                        summary += f"  • Active Ports: {len(active_ports)}\n"
                        
                        # Show details for first few active ports
                        for port in active_ports[:3]:
                            port_idx = port.get("port_idx", "?")
                            speed = port.get("speed", "Unknown")
                            full_duplex = port.get("full_duplex", False)
                            duplex_str = "Full" if full_duplex else "Half"
                            
                            summary += f"  • Port {port_idx}: {speed} Mbps ({duplex_str} Duplex)\n"
                        
                        if len(active_ports) > 3:
                            summary += f"  • ... and {len(active_ports) - 3} more active ports\n"
                        summary += "\n"
                    
                    # Create concise stats summary
                    stats_data = {
                        "name": name,
                        "model": model,
                        "mac": device.get('mac', '').upper(),
                        "uptime": uptime_str,
                        "system": {
                            "cpu": f"{system_stats.get('cpu', 'Unknown')}%" if system_stats.get('cpu') != "Unknown" else "Unknown",
                            "memory": f"{system_stats.get('mem', 'Unknown')}%" if system_stats.get('mem') != "Unknown" else "Unknown"
                        },
                        "traffic": {
                            "total_bytes": tx_bytes + rx_bytes,
                            "tx_packets": tx_packets,
                            "rx_packets": rx_packets
                        }
                    }
                    
                    # Add device-specific stats
                    device_type = device.get('type', '')
                    if device_type == 'uap' and radio_table:
                        stats_data["radio_count"] = len(radio_table)
                    elif device_type == 'usw' and port_table:
                        stats_data["active_ports"] = len(active_ports)
                        stats_data["total_ports"] = len(port_table)
                    
                    return json.dumps(stats_data, indent=2)
            
            return f"**Device Not Found**\n\nNo device with MAC address {mac} found in site {site_name}."
            
        except Exception as e:
            logger.error(f"Error in device stats resource for {mac}: {e}")
            return f"Error retrieving device statistics for {mac}: {str(e)}"
    
    
    @mcp.resource("unifi://device-tags")
    async def resource_device_tags():
        """Get device tags with clean formatting (default site)."""
        try:
            tags = await client._make_request("GET", "/rest/tag", site_name="default")
            
            if isinstance(tags, dict) and "error" in tags:
                return f"Error retrieving device tags: {tags['error']}"
            
            if not isinstance(tags, list):
                return "Error: Unexpected response format"
            
            # Filter tags to essential info only
            filtered_tags = []
            for tag in tags:
                filtered_tag = {
                    "name": tag.get("name", "Unknown"),
                    "id": tag.get("_id", "Unknown"),
                    "device_count": len(tag.get("member_table", [])),
                    "color": tag.get("attr_color", "default")
                }
                filtered_tags.append(filtered_tag)
            
            return json.dumps(filtered_tags, indent=2)
            
        except Exception as e:
            logger.error(f"Error in device tags resource: {e}")
            return f"Error retrieving device tags: {str(e)}"
    
    
    @mcp.resource("unifi://device-tags/{site_name}")
    async def resource_site_device_tags(site_name: str):
        """Get device tags with clean formatting for specific site."""
        try:
            tags = await client._make_request("GET", "/rest/tag", site_name=site_name)
            
            if isinstance(tags, dict) and "error" in tags:
                return f"Error retrieving device tags for site {site_name}: {tags['error']}"
            
            if not isinstance(tags, list):
                return "Error: Unexpected response format"
            
            # Filter tags to essential info only
            filtered_tags = []
            for tag in tags:
                filtered_tag = {
                    "name": tag.get("name", "Unknown"),
                    "id": tag.get("_id", "Unknown"),
                    "device_count": len(tag.get("member_table", [])),
                    "color": tag.get("attr_color", "default")
                }
                filtered_tags.append(filtered_tag)
                
            return json.dumps(filtered_tags, indent=2)
            
        except Exception as e:
            logger.error(f"Error in site device tags resource: {e}")
            return f"Error retrieving device tags for site {site_name}: {str(e)}"
