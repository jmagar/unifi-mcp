"""
Client management tools for UniFi MCP Server.

Provides tools for listing and managing UniFi network clients.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_client_summary

logger = logging.getLogger(__name__)


def register_client_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all client management tools."""
    
    @mcp.tool()
    async def get_clients(connected_only: bool = True, site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get connected clients with formatted connection details.
        
        Args:
            connected_only: Only return currently connected clients (default: True)
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of clients with essential connection information
        """
        try:
            clients = await client.get_clients(site_name)
            
            if isinstance(clients, dict) and "error" in clients:
                return [clients]
            
            if not isinstance(clients, list):
                return [{"error": "Unexpected response format"}]
            
            # Format each client for clean output
            formatted_clients = []
            for client_data in clients:
                try:
                    # Skip offline clients if connected_only is True
                    if connected_only and not client_data.get("is_online", True):
                        continue
                    
                    formatted_client = format_client_summary(client_data)
                    formatted_clients.append(formatted_client)
                except Exception as e:
                    logger.error(f"Error formatting client {client_data.get('name', 'Unknown')}: {e}")
                    formatted_clients.append({
                        "name": client_data.get("name", "Unknown"),
                        "mac": client_data.get("mac", ""),
                        "error": f"Formatting error: {str(e)}"
                    })
            
            return formatted_clients
            
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def reconnect_client(mac: str, site_name: str = "default") -> Dict[str, Any]:
        """
        Force reconnection of a client device.
        
        Args:
            mac: Client MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the reconnect operation
        """
        try:
            result = await client.reconnect_client(mac, site_name)
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {
                "success": True,
                "message": f"Client {mac} reconnect command sent",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error reconnecting client {mac}: {e}")
            return {"error": str(e)}