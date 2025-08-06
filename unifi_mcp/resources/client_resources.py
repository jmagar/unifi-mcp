"""
Client-related MCP resources for UniFi MCP Server.

Provides structured access to client information and connection details.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_generic_list

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
            
            return format_generic_list(clients_data, "Connected Clients", ["name", "ip", "is_wired", "rssi"])
            
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
            
            return format_generic_list(clients_data, "Connected Clients", ["name", "ip", "is_wired", "rssi"])
            
        except Exception as e:
            logger.error(f"Error in site clients resource for {site_name}: {e}")
            return f"Error retrieving clients for site {site_name}: {str(e)}"