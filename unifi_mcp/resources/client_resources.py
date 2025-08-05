"""
Client-related MCP resources for UniFi MCP Server.

Provides structured access to client information and connection details.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_client_summary

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
            
            formatted_clients = [format_client_summary(client_info) for client_info in clients_data]
            
            if not formatted_clients:
                return "**UniFi Connected Clients**\n\nNo clients currently connected."
            
            # Group clients by connection type
            wireless_clients = [c for c in formatted_clients if c.get('connection_type') == 'Wireless']
            wired_clients = [c for c in formatted_clients if c.get('connection_type') == 'Wired']
            
            summary = f"**UniFi Connected Clients** ({len(formatted_clients)} total)\n\n"
            
            if wireless_clients:
                summary += f"**📶 Wireless Clients** ({len(wireless_clients)})\n"
                for client_info in wireless_clients[:10]:  # Limit to 10 for readability
                    name = client_info.get('name', 'Unknown Device')
                    if not name:
                        name = client_info.get('device_type', 'Unknown Device')
                    ip = client_info.get('ip', 'No IP')
                    signal = client_info.get('signal_strength', 'Unknown signal')
                    connected_time = client_info.get('connected_time', 'Unknown')
                    summary += f"• **{name}** ({ip}) - {signal}, Connected: {connected_time}\n"
                
                if len(wireless_clients) > 10:
                    summary += f"• ... and {len(wireless_clients) - 10} more wireless clients\n"
                summary += "\n"
            
            if wired_clients:
                summary += f"**🔌 Wired Clients** ({len(wired_clients)})\n"
                for client_info in wired_clients[:5]:  # Limit to 5 for readability
                    name = client_info.get('name', 'Unknown Device')
                    if not name:
                        name = client_info.get('device_type', 'Unknown Device')
                    ip = client_info.get('ip', 'No IP')
                    port_speed = client_info.get('port_speed', 'Unknown speed')
                    connected_time = client_info.get('connected_time', 'Unknown')
                    summary += f"• **{name}** ({ip}) - {port_speed}, Connected: {connected_time}\n"
                
                if len(wired_clients) > 5:
                    summary += f"• ... and {len(wired_clients) - 5} more wired clients\n"
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error in clients resource: {e}")
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
            
            formatted_clients = [format_client_summary(client_info) for client_info in clients_data]
            
            if not formatted_clients:
                return f"**UniFi Connected Clients - {site_name}**\n\nNo clients currently connected."
            
            # Group clients by connection type
            wireless_clients = [c for c in formatted_clients if c.get('connection_type') == 'Wireless']
            wired_clients = [c for c in formatted_clients if c.get('connection_type') == 'Wired']
            
            summary = f"**UniFi Connected Clients - {site_name}** ({len(formatted_clients)} total)\n\n"
            
            if wireless_clients:
                summary += f"**📶 Wireless Clients** ({len(wireless_clients)})\n"
                for client_info in wireless_clients[:10]:  # Limit to 10 for readability
                    name = client_info.get('name', 'Unknown Device')
                    if not name:
                        name = client_info.get('device_type', 'Unknown Device')
                    ip = client_info.get('ip', 'No IP')
                    signal = client_info.get('signal_strength', 'Unknown signal')
                    connected_time = client_info.get('connected_time', 'Unknown')
                    summary += f"• **{name}** ({ip}) - {signal}, Connected: {connected_time}\n"
                
                if len(wireless_clients) > 10:
                    summary += f"• ... and {len(wireless_clients) - 10} more wireless clients\n"
                summary += "\n"
            
            if wired_clients:
                summary += f"**🔌 Wired Clients** ({len(wired_clients)})\n"
                for client_info in wired_clients[:5]:  # Limit to 5 for readability
                    name = client_info.get('name', 'Unknown Device')
                    if not name:
                        name = client_info.get('device_type', 'Unknown Device')
                    ip = client_info.get('ip', 'No IP')
                    port_speed = client_info.get('port_speed', 'Unknown speed')
                    connected_time = client_info.get('connected_time', 'Unknown')
                    summary += f"• **{name}** ({ip}) - {port_speed}, Connected: {connected_time}\n"
                
                if len(wired_clients) > 5:
                    summary += f"• ... and {len(wired_clients) - 5} more wired clients\n"
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error in site clients resource for {site_name}: {e}")
            return f"Error retrieving clients for site {site_name}: {str(e)}"