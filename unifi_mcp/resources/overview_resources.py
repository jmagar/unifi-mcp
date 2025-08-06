"""
Overview MCP resources for UniFi MCP Server.

Provides comprehensive dashboard and overview resources with glanceable information.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import get_device_type_name, format_data_values, format_generic_list

logger = logging.getLogger(__name__)


def register_overview_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register overview and dashboard MCP resources."""
    
    @mcp.resource("unifi://dashboard")
    async def resource_dashboard():
        """Get dashboard metrics with clean formatting (default site)."""
        try:
            dashboard = await client.get_dashboard_metrics("default")
            
            if isinstance(dashboard, dict) and "error" in dashboard:
                return f"Error retrieving dashboard: {dashboard['error']}"
            
            # Handle both dict and list formats - dashboard might return list of time-series data
            if isinstance(dashboard, list):
                if not dashboard:
                    return "**UniFi Dashboard Metrics**\n\nNo dashboard data available."
                
                # Use the most recent data point
                latest_data = dashboard[-1] if dashboard else {}
                
                summary = "**UniFi Dashboard Metrics** (Latest Data Point)\n\n"
                
                # Extract WAN traffic if available
                wan_tx = latest_data.get("wan-tx_bytes", latest_data.get("tx_bytes-r", 0))
                wan_rx = latest_data.get("wan-rx_bytes", latest_data.get("rx_bytes-r", 0))
                if wan_tx > 0 or wan_rx > 0:
                    formatted_wan = format_data_values({
                        "tx": wan_tx,
                        "rx": wan_rx,
                        "total": wan_tx + wan_rx
                    })
                    
                    summary += "🌐 **WAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wan.get('rx', '0 B')}/s\n\n"
                
                # Extract wireless traffic if available
                wlan_tx = latest_data.get("tx_bytes-r", 0)
                wlan_rx = latest_data.get("rx_bytes-r", 0)
                if wlan_tx > 0 or wlan_rx > 0:
                    formatted_wlan = format_data_values({
                        "tx": wlan_tx,
                        "rx": wlan_rx,
                        "total": wlan_tx + wlan_rx
                    })
                    
                    summary += "📶 **WLAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wlan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wlan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wlan.get('rx', '0 B')}/s\n\n"
                
                # Additional metrics if available
                if "latency_avg" in latest_data:
                    latency = latest_data.get("latency_avg", 0)
                    summary += f"⏱️ **Network Latency**: {latency:.1f}ms average\n\n"
                
                # Add note about time-series data
                summary += f"*Data from {len(dashboard)} time points - showing latest measurements*"
                
                return format_generic_list([dashboard[-1]], "Dashboard Metrics", ["wan-tx_bytes", "wan-rx_bytes", "time"])
            
            elif isinstance(dashboard, dict):
                summary = "**UniFi Dashboard Metrics**\n\n"
                
                # Extract key metrics if available
                if "wan" in dashboard:
                    wan_data = dashboard["wan"]
                    wan_tx = wan_data.get("tx_bytes-r", 0)
                    wan_rx = wan_data.get("rx_bytes-r", 0)
                    wan_total = wan_tx + wan_rx
                    
                    formatted_wan = format_data_values({
                        "total": wan_total,
                        "tx": wan_tx,
                        "rx": wan_rx
                    })
                    
                    summary += "🌐 **WAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wan.get('rx', '0 B')}/s\n\n"
                
                if "wlan" in dashboard:
                    wlan_data = dashboard["wlan"]
                    wlan_tx = wlan_data.get("tx_bytes-r", 0)
                    wlan_rx = wlan_data.get("rx_bytes-r", 0)
                    wlan_total = wlan_tx + wlan_rx
                    
                    formatted_wlan = format_data_values({
                        "total": wlan_total,
                        "tx": wlan_tx,
                        "rx": wlan_rx
                    })
                    
                    summary += "📶 **WLAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wlan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wlan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wlan.get('rx', '0 B')}/s\n\n"
                
                if "num_clients" in dashboard:
                    num_clients = dashboard["num_clients"]
                    summary += f"👥 **Connected Clients**: {num_clients}\n\n"
                
                if "num_aps" in dashboard:
                    num_aps = dashboard["num_aps"]
                    summary += f"📡 **Access Points**: {num_aps}\n\n"
                
                # Add note about real-time data
                summary += "*Real-time traffic rates updated every few seconds*"
                
                return format_generic_list([dashboard], "Dashboard Data", ["tx_bytes-r", "rx_bytes-r", "time"])
            
            else:
                return "**UniFi Dashboard Metrics**\n\nUnexpected dashboard data format received."
            
        except Exception as e:
            logger.error(f"Error in dashboard resource: {e}")
            return f"Error retrieving dashboard: {str(e)}"
    
    
    @mcp.resource("unifi://dashboard/{site_name}")
    async def resource_site_dashboard(site_name: str):
        """Get dashboard metrics with clean formatting for specific site."""
        try:
            dashboard = await client.get_dashboard_metrics(site_name)
            
            if isinstance(dashboard, dict) and "error" in dashboard:
                return f"Error retrieving dashboard for site {site_name}: {dashboard['error']}"
            
            # Handle both dict and list formats - dashboard might return list of time-series data
            if isinstance(dashboard, list):
                if not dashboard:
                    return f"**UniFi Dashboard Metrics - {site_name}**\n\nNo dashboard data available."
                
                # Use the most recent data point
                latest_data = dashboard[-1] if dashboard else {}
                
                summary = f"**UniFi Dashboard Metrics - {site_name}** (Latest Data Point)\n\n"
                
                # Extract WAN traffic if available
                wan_tx = latest_data.get("wan-tx_bytes", latest_data.get("tx_bytes-r", 0))
                wan_rx = latest_data.get("wan-rx_bytes", latest_data.get("rx_bytes-r", 0))
                if wan_tx > 0 or wan_rx > 0:
                    formatted_wan = format_data_values({
                        "tx": wan_tx,
                        "rx": wan_rx,
                        "total": wan_tx + wan_rx
                    })
                    
                    summary += "🌐 **WAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wan.get('rx', '0 B')}/s\n\n"
                
                # Extract wireless traffic if available
                wlan_tx = latest_data.get("tx_bytes-r", 0)
                wlan_rx = latest_data.get("rx_bytes-r", 0)
                if wlan_tx > 0 or wlan_rx > 0:
                    formatted_wlan = format_data_values({
                        "tx": wlan_tx,
                        "rx": wlan_rx,
                        "total": wlan_tx + wlan_rx
                    })
                    
                    summary += "📶 **WLAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wlan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wlan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wlan.get('rx', '0 B')}/s\n\n"
                
                # Additional metrics if available
                if "latency_avg" in latest_data:
                    latency = latest_data.get("latency_avg", 0)
                    summary += f"⏱️ **Network Latency**: {latency:.1f}ms average\n\n"
                
                # Add note about time-series data
                summary += f"*Data from {len(dashboard)} time points - showing latest measurements*"
                
                return format_generic_list([dashboard[-1]], "Site Dashboard Metrics", ["wan-tx_bytes", "wan-rx_bytes", "time"])
            
            elif isinstance(dashboard, dict):
                summary = f"**UniFi Dashboard Metrics - {site_name}**\n\n"
                
                # Extract key metrics if available
                if "wan" in dashboard:
                    wan_data = dashboard["wan"]
                    wan_tx = wan_data.get("tx_bytes-r", 0)
                    wan_rx = wan_data.get("rx_bytes-r", 0)
                    wan_total = wan_tx + wan_rx
                    
                    formatted_wan = format_data_values({
                        "total": wan_total,
                        "tx": wan_tx,
                        "rx": wan_rx
                    })
                    
                    summary += "🌐 **WAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wan.get('rx', '0 B')}/s\n\n"
                
                if "wlan" in dashboard:
                    wlan_data = dashboard["wlan"]
                    wlan_tx = wlan_data.get("tx_bytes-r", 0)
                    wlan_rx = wlan_data.get("rx_bytes-r", 0)
                    wlan_total = wlan_tx + wlan_rx
                    
                    formatted_wlan = format_data_values({
                        "total": wlan_total,
                        "tx": wlan_tx,
                        "rx": wlan_rx
                    })
                    
                    summary += "📶 **WLAN Traffic (Real-time)**\n"
                    summary += f"  • Total: {formatted_wlan.get('total', '0 B')}/s\n"
                    summary += f"  • Upload: {formatted_wlan.get('tx', '0 B')}/s\n"
                    summary += f"  • Download: {formatted_wlan.get('rx', '0 B')}/s\n\n"
                
                if "num_clients" in dashboard:
                    num_clients = dashboard["num_clients"]
                    summary += f"👥 **Connected Clients**: {num_clients}\n\n"
                
                if "num_aps" in dashboard:
                    num_aps = dashboard["num_aps"]
                    summary += f"📡 **Access Points**: {num_aps}\n\n"
                
                # Add note about real-time data
                summary += "*Real-time traffic rates updated every few seconds*"
                
                return format_generic_list([dashboard], "Site Dashboard Data", ["tx_bytes-r", "rx_bytes-r", "time"])
            
            else:
                return f"**UniFi Dashboard Metrics - {site_name}**\n\nUnexpected dashboard data format received."
            
        except Exception as e:
            logger.error(f"Error in site dashboard resource for {site_name}: {e}")
            return f"Error retrieving dashboard for site {site_name}: {str(e)}"
    
    
    @mcp.resource("unifi://overview")
    async def resource_overview():
        """Get comprehensive network overview with clean formatting (default site)."""
        try:
            # Gather all overview data
            devices = await client.get_devices("default")
            clients = await client.get_clients("default")
            
            # Handle errors in critical requests
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices: {devices['error']}"
            if isinstance(clients, dict) and "error" in clients:
                return f"Error retrieving clients: {clients['error']}"
            
            # Ensure we have lists
            if not isinstance(devices, list):
                devices = []
            if not isinstance(clients, list):
                clients = []
            
            # Get additional data (non-critical)
            try:
                port_forwarding = await client.get_port_forwarding_rules("default")
                if isinstance(port_forwarding, dict) and "error" in port_forwarding:
                    port_forwarding = []
                elif not isinstance(port_forwarding, list):
                    port_forwarding = []
            except Exception:
                port_forwarding = []
            
            summary = "**UniFi Network Overview**\n\n"
            
            # Device summary
            device_counts = {"Gateway": 0, "Access Point": 0, "Switch": 0, "Other": 0}
            online_devices = 0
            gateway_info = None
            
            for device in devices:
                device_type = get_device_type_name(device)
                state = device.get("state", 0)
                
                if device_type in device_counts:
                    device_counts[device_type] += 1
                else:
                    device_counts["Other"] += 1
                
                if state == 1:  # Online
                    online_devices += 1
                
                # Capture gateway info
                if device_type == "Gateway" and state == 1:
                    gateway_info = {
                        "name": device.get("name", "Gateway"),
                        "model": device.get("model", "Unknown"),
                        "wan_ip": device.get("wan1", {}).get("ip", "Unknown"),
                        "lan_ip": device.get("lan_ip", "Unknown"),
                        "uptime": device.get("uptime", 0),
                        "version": device.get("version", "Unknown")
                    }
            
            # Network devices summary
            summary += "🏭 **Network Infrastructure**\n"
            summary += f"  • Total Devices: {len(devices)} ({online_devices} online)\n"
            if device_counts["Gateway"] > 0:
                summary += f"  • 🌐 Gateways: {device_counts['Gateway']}\n"
            if device_counts["Access Point"] > 0:
                summary += f"  • 📡 Access Points: {device_counts['Access Point']}\n"
            if device_counts["Switch"] > 0:
                summary += f"  • 🔌 Switches: {device_counts['Switch']}\n"
            summary += "\n"
            
            # Gateway information
            if gateway_info:
                uptime = gateway_info["uptime"]
                if isinstance(uptime, (int, float)):
                    days = int(uptime // 86400)
                    hours = int((uptime % 86400) // 3600)
                    uptime_str = f"{days}d {hours}h"
                else:
                    uptime_str = "Unknown"
                
                summary += f"🌐 **Gateway ({gateway_info['name']})**\n"
                summary += f"  • Model: {gateway_info['model']}\n"
                summary += f"  • WAN IP: {gateway_info['wan_ip']}\n"
                summary += f"  • LAN IP: {gateway_info['lan_ip']}\n"
                summary += f"  • Uptime: {uptime_str}\n"
                summary += f"  • Version: {gateway_info['version']}\n\n"
            
            # Client summary
            wireless_clients = [c for c in clients if not c.get('is_wired', True)]
            wired_clients = [c for c in clients if c.get('is_wired', True)]
            
            summary += f"👥 **Connected Clients** ({len(clients)} total)\n"
            if wireless_clients:
                summary += f"  • 📶 Wireless: {len(wireless_clients)}\n"
            if wired_clients:
                summary += f"  • 🔌 Wired: {len(wired_clients)}\n"
            summary += "\n"
            
            # Port forwarding summary
            if port_forwarding:
                enabled_rules = [r for r in port_forwarding if r.get('enabled', False)]
                summary += "🚪 **Port Forwarding**\n"
                summary += f"  • Total Rules: {len(port_forwarding)}\n"
                summary += f"  • Enabled Rules: {len(enabled_rules)}\n\n"
            
            return format_generic_list(devices + clients, "Network Overview", ["name", "type", "status"])
            
        except Exception as e:
            logger.error(f"Error in overview resource: {e}")
            return f"Error retrieving network overview: {str(e)}"
    
    
    @mcp.resource("unifi://overview/{site_name}")
    async def resource_site_overview(site_name: str):
        """Get comprehensive network overview with clean formatting for specific site."""
        try:
            # Gather all overview data
            devices = await client.get_devices(site_name)
            clients = await client.get_clients(site_name)
            
            # Handle errors in critical requests
            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices for site {site_name}: {devices['error']}"
            if isinstance(clients, dict) and "error" in clients:
                return f"Error retrieving clients for site {site_name}: {clients['error']}"
            
            # Ensure we have lists
            if not isinstance(devices, list):
                devices = []
            if not isinstance(clients, list):
                clients = []
            
            # Get additional data (non-critical)
            try:
                port_forwarding = await client.get_port_forwarding_rules(site_name)
                if isinstance(port_forwarding, dict) and "error" in port_forwarding:
                    port_forwarding = []
                elif not isinstance(port_forwarding, list):
                    port_forwarding = []
            except Exception:
                port_forwarding = []
            
            summary = f"**UniFi Network Overview - {site_name}**\n\n"
            
            # Device summary
            device_counts = {"Gateway": 0, "Access Point": 0, "Switch": 0, "Other": 0}
            online_devices = 0
            gateway_info = None
            
            for device in devices:
                device_type = get_device_type_name(device)
                state = device.get("state", 0)
                
                if device_type in device_counts:
                    device_counts[device_type] += 1
                else:
                    device_counts["Other"] += 1
                
                if state == 1:  # Online
                    online_devices += 1
                
                # Capture gateway info
                if device_type == "Gateway" and state == 1:
                    gateway_info = {
                        "name": device.get("name", "Gateway"),
                        "model": device.get("model", "Unknown"),
                        "wan_ip": device.get("wan1", {}).get("ip", "Unknown"),
                        "lan_ip": device.get("lan_ip", "Unknown"),
                        "uptime": device.get("uptime", 0),
                        "version": device.get("version", "Unknown")
                    }
            
            # Network devices summary
            summary += "🏭 **Network Infrastructure**\n"
            summary += f"  • Total Devices: {len(devices)} ({online_devices} online)\n"
            if device_counts["Gateway"] > 0:
                summary += f"  • 🌐 Gateways: {device_counts['Gateway']}\n"
            if device_counts["Access Point"] > 0:
                summary += f"  • 📡 Access Points: {device_counts['Access Point']}\n"
            if device_counts["Switch"] > 0:
                summary += f"  • 🔌 Switches: {device_counts['Switch']}\n"
            summary += "\n"
            
            # Gateway information
            if gateway_info:
                uptime = gateway_info["uptime"]
                if isinstance(uptime, (int, float)):
                    days = int(uptime // 86400)
                    hours = int((uptime % 86400) // 3600)
                    uptime_str = f"{days}d {hours}h"
                else:
                    uptime_str = "Unknown"
                
                summary += f"🌐 **Gateway ({gateway_info['name']})**\n"
                summary += f"  • Model: {gateway_info['model']}\n"
                summary += f"  • WAN IP: {gateway_info['wan_ip']}\n"
                summary += f"  • LAN IP: {gateway_info['lan_ip']}\n"
                summary += f"  • Uptime: {uptime_str}\n"
                summary += f"  • Version: {gateway_info['version']}\n\n"
            
            # Client summary
            wireless_clients = [c for c in clients if not c.get('is_wired', True)]
            wired_clients = [c for c in clients if c.get('is_wired', True)]
            
            summary += f"👥 **Connected Clients** ({len(clients)} total)\n"
            if wireless_clients:
                summary += f"  • 📶 Wireless: {len(wireless_clients)}\n"
            if wired_clients:
                summary += f"  • 🔌 Wired: {len(wired_clients)}\n"
            summary += "\n"
            
            # Port forwarding summary
            if port_forwarding:
                enabled_rules = [r for r in port_forwarding if r.get('enabled', False)]
                summary += "🚪 **Port Forwarding**\n"
                summary += f"  • Total Rules: {len(port_forwarding)}\n"
                summary += f"  • Enabled Rules: {len(enabled_rules)}\n\n"
            
            return format_generic_list(devices + clients, "Site Network Overview", ["name", "type", "status"])
            
        except Exception as e:
            logger.error(f"Error in site overview resource for {site_name}: {e}")
            return f"Error retrieving network overview for site {site_name}: {str(e)}"