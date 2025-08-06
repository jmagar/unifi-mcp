"""
Device-related MCP resources for UniFi MCP Server.

Provides structured access to device information and statistics.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_generic_list, format_data_values

logger = logging.getLogger(__name__)


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
            
            return format_generic_list(devices, "UniFi Network Devices", ["name", "model", "state", "uptime"])
            
        except Exception as e:
            return f"Error retrieving devices: {str(e)}"
    
    
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
                    try:
                        name = device.get('name', 'Unknown Device')
                        model = device.get('model', 'Unknown Model')
                        device_mac_display = device.get('mac', 'Unknown MAC')
                        state = 'Online' if device.get('state', 0) == 1 else 'Offline'
                        uptime = device.get('uptime', 0)
                        ip = device.get('ip', 'Unknown')
                        
                        # Determine device icon and type
                        device_type = device.get('type', '')
                        if device_type == 'uap':
                            icon = "📡"
                            type_name = "Access Point"
                        elif device_type == 'ugw':
                            icon = "🌐"
                            type_name = "Gateway"
                        elif device_type == 'usw':
                            icon = "🔌"
                            type_name = "Switch"
                        else:
                            icon = "📱"
                            type_name = "Device"
                        
                        summary = f"**{icon} {name}** ({type_name})\n\n"
                        summary += "**Device Information:**\n"
                        summary += f"  • Model: {model}\n"
                        summary += f"  • MAC: {device_mac_display}\n"
                        summary += f"  • IP Address: {ip}\n"
                        summary += f"  • Status: {state}\n"
                        summary += f"  • Uptime: {uptime}\n"
                        
                        # Add device-specific details
                        if device_type == 'uap':  # Access Point
                            num_clients = device.get('num_sta', 0)
                            summary += f"  • Connected Clients: {num_clients}\n"
                            
                        elif device_type == 'usw':  # Switch
                            port_table = device.get('port_table', [])
                            active_ports = len([p for p in port_table if p.get('up', False)])
                            summary += f"  • Active Ports: {active_ports}/{len(port_table)}\n"
                            
                        elif device_type == 'ugw':  # Gateway
                            wan_info = device.get('wan1', {})
                            if wan_info:
                                wan_ip = wan_info.get('ip', 'Unknown')
                                summary += f"  • WAN IP: {wan_ip}\n"
                        
                        return format_generic_list([device], "Device Details", ["name", "model", "state", "ip"])
                        
                    except Exception as format_error:
                        return f"**Device Found** (MAC: {mac})\n\nError formatting device details: {str(format_error)}"
            
            return f"**Device Not Found**\n\nNo device with MAC address {mac} found in site {site_name}."
            
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
                    
                    # Create stats summary data
                    stats_data = {
                        "name": name,
                        "uptime": uptime_str,
                        "cpu": system_stats.get("cpu", "Unknown"),
                        "memory": system_stats.get("mem", "Unknown")
                    }
                    return format_generic_list([stats_data], "Device Statistics", ["name", "uptime", "cpu", "memory"])
            
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
            
            if not tags:
                return "**UniFi Device Tags**\n\nNo device tags configured."
            
            summary = f"**UniFi Device Tags** ({len(tags)} total)\n\n"
            
            for tag in tags:
                name = tag.get("name", "Unknown Tag")
                color = tag.get("color", "default")
                members = tag.get("member_table", [])
                
                # Map color to emoji (approximate)
                color_emoji = {
                    "red": "🔴",
                    "orange": "🟠",
                    "yellow": "🟡",
                    "green": "🟢",
                    "blue": "🔵",
                    "purple": "🟣",
                    "gray": "⚫",
                    "grey": "⚫"
                }.get(color.lower(), "🏷️")
                
                summary += f"{color_emoji} **{name}**\n"
                summary += f"  • Color: {color.title()}\n"
                summary += f"  • Devices: {len(members)}\n"
                
                # Show first few device names if available
                if members:
                    device_names = []
                    for member in members[:3]:  # Show first 3 devices
                        device_name = member.get("name", member.get("mac", "Unknown"))
                        device_names.append(device_name)
                    
                    summary += f"  • Tagged Devices: {', '.join(device_names)}"
                    if len(members) > 3:
                        summary += f" (+{len(members) - 3} more)"
                    summary += "\n"
                
                summary += "\n"
            
            return format_generic_list(tags, "Device Tags", ["name", "color"])
            
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
            
            if not tags:
                return f"**UniFi Device Tags - {site_name}**\n\nNo device tags configured."
            
            summary = f"**UniFi Device Tags - {site_name}** ({len(tags)} total)\n\n"
            
            for tag in tags:
                name = tag.get("name", "Unknown Tag")
                color = tag.get("color", "default")
                members = tag.get("member_table", [])
                
                # Map color to emoji (approximate)
                color_emoji = {
                    "red": "🔴",
                    "orange": "🟠",
                    "yellow": "🟡",
                    "green": "🟢",
                    "blue": "🔵",
                    "purple": "🟣",
                    "gray": "⚫",
                    "grey": "⚫"
                }.get(color.lower(), "🏷️")
                
                summary += f"{color_emoji} **{name}**\n"
                summary += f"  • Color: {color.title()}\n"
                summary += f"  • Devices: {len(members)}\n"
                
                # Show first few device names if available
                if members:
                    device_names = []
                    for member in members[:3]:  # Show first 3 devices
                        device_name = member.get("name", member.get("mac", "Unknown"))
                        device_names.append(device_name)
                    
                    summary += f"  • Tagged Devices: {', '.join(device_names)}"
                    if len(members) > 3:
                        summary += f" (+{len(members) - 3} more)"
                    summary += "\n"
                
                summary += "\n"
            
            return format_generic_list(tags, "Site Device Tags", ["name", "color"])
            
        except Exception as e:
            logger.error(f"Error in site device tags resource for {site_name}: {e}")
            return f"Error retrieving device tags for site {site_name}: {str(e)}"