"""
Client-related MCP resources for UniFi MCP Server.

Provides structured access to client information and connection details.
"""

import json
import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient

def filter_client_data(clients):
    """Filter client data to show only essential information."""
    filtered_clients = []
    
    for client in clients:
        filtered_client = {
            "name": client.get("name") or client.get("hostname", "Unknown Device"),
            "mac": client.get("mac", "Unknown"),
            "ip": client.get("ip", "Unknown"),
            "connection_type": "Wired" if client.get("is_wired", False) else "Wireless",
            "uptime": format_client_uptime(client.get("uptime", 0)),
            "last_seen": format_client_uptime(client.get("last_seen", 0), from_timestamp=True),
            "network": client.get("network", "Unknown")
        }
        
        # Add wireless-specific info
        if not client.get("is_wired", False):
            filtered_client["signal"] = f"{client.get('rssi', 'Unknown')} dBm"
            filtered_client["access_point"] = client.get("last_uplink_name", "Unknown")
            
        # Add device type info
        if client.get("dev_vendor"):
            filtered_client["vendor"] = get_vendor_name(client.get("oui", ""))
            
        filtered_clients.append(filtered_client)
    
    return filtered_clients

def format_client_uptime(uptime, from_timestamp=False):
    """Format uptime in human readable format."""
    if from_timestamp and uptime > 0:
        # Convert timestamp to "time ago"
        import time
        seconds_ago = int(time.time()) - uptime
        if seconds_ago < 60:
            return "Just now"
        elif seconds_ago < 3600:
            return f"{seconds_ago // 60}m ago"
        elif seconds_ago < 86400:
            return f"{seconds_ago // 3600}h ago"
        else:
            return f"{seconds_ago // 86400}d ago"
    elif isinstance(uptime, (int, float)) and uptime > 0:
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        if days > 0:
            return f"{days}d {hours}h"
        else:
            return f"{hours}h"
    return "Unknown"

def get_vendor_name(oui):
    """Get simplified vendor name from OUI."""
    if not oui:
        return "Unknown"
    # Simplify common vendor names
    if "Apple" in oui:
        return "Apple"
    elif "Google" in oui:
        return "Google"
    elif "Samsung" in oui:
        return "Samsung"
    elif "Intel" in oui:
        return "Intel"
    else:
        return oui.split(",")[0] if "," in oui else oui

logger = logging.getLogger(__name__)


def register_client_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all client-related MCP resources."""
    
    @mcp.resource("unifi://clients")
    async def resource_all_clients():
        """Get all connected clients with clean formatting."""
        try:
            clients_data = await client.get_clients("default")
            
            if isinstance(clients_data, dict) and "error" in clients_data:
                return f"Error retrieving clients: {clients_data['error']}"
            
            if not isinstance(clients_data, list):
                return "Error: Unexpected response format"
            
            filtered_clients = filter_client_data(clients_data)
            return json.dumps(filtered_clients, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"Error retrieving clients: {str(e)}"
    
    
    @mcp.resource("unifi://clients/{site_name}")
    async def resource_site_clients(site_name: str):
        """Get clients with clean formatting for specific site."""
        try:
            clients_data = await client.get_clients(site_name)
            
            if isinstance(clients_data, dict) and "error" in clients_data:
                return f"Error retrieving clients for site {site_name}: {clients_data['error']}"
            
            if not isinstance(clients_data, list):
                return "Error: Unexpected response format"
            
            filtered_clients = filter_client_data(clients_data)
            return json.dumps(filtered_clients, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in site clients resource for {site_name}: {e}")
            return f"Error retrieving clients for site {site_name}: {str(e)}"