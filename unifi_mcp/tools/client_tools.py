"""
Client management tools for UniFi MCP Server.

Provides tools for listing and managing UniFi network clients.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..client import UnifiControllerClient
from ..formatters import format_client_summary, format_clients_list

logger = logging.getLogger(__name__)


def register_client_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all client management tools."""
    
    @mcp.tool()
    async def get_clients(connected_only: bool = True, site_name: str = "default") -> ToolResult:
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
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {clients.get('error','unknown error')}")],
                    structured_content=[clients]
                )
            
            if not isinstance(clients, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content=[{"error": "Unexpected response format"}]
                )
            
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
            
            summary_text = format_clients_list(
                [c for c in clients if (c.get("is_online", True) or not connected_only)]
            )
            return ToolResult(
                content=[TextContent(type="text", text=summary_text)],
                structured_content=formatted_clients
            )
            
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content=[{"error": str(e)}]
            )
    
    
    @mcp.tool()
    async def reconnect_client(mac: str, site_name: str = "default") -> ToolResult:
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
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Client {mac} reconnect command sent",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Reconnect requested: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error reconnecting client {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def block_client(mac: str, site_name: str = "default") -> ToolResult:
        """
        Block a client from accessing the network.
        
        Args:
            mac: Client MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the block operation
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            result = await client._make_request("POST", "/cmd/stamgr", 
                                               site_name=site_name, 
                                               data={"cmd": "block-sta", "mac": normalized_mac})
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Client {mac} has been blocked from network access",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Blocked client: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error blocking client {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def unblock_client(mac: str, site_name: str = "default") -> ToolResult:
        """
        Unblock a previously blocked client.
        
        Args:
            mac: Client MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the unblock operation
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            result = await client._make_request("POST", "/cmd/stamgr", 
                                               site_name=site_name, 
                                               data={"cmd": "unblock-sta", "mac": normalized_mac})
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Client {mac} has been unblocked and can access the network",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Unblocked client: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error unblocking client {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def forget_client(mac: str, site_name: str = "default") -> ToolResult:
        """
        Remove historical data for a client (GDPR compliance).
        
        Args:
            mac: Client MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the forget operation
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            result = await client._make_request("POST", "/cmd/stamgr", 
                                               site_name=site_name, 
                                               data={"cmd": "forget-sta", "macs": [normalized_mac]})
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Client {mac} historical data has been removed",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Forgot client data: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error forgetting client {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def set_client_name(mac: str, name: str, site_name: str = "default") -> ToolResult:
        """
        Set or update the name/alias for a client.
        
        Args:
            mac: Client MAC address (any format)
            name: New name for the client (empty string to remove)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the name update operation
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # First get the client to find its ID
            clients = await client.get_clients(site_name)
            client_id = None
            
            if isinstance(clients, list):
                for client_data in clients:
                    if client_data.get("mac", "").lower().replace("-", ":").replace(".", ":") == normalized_mac:
                        client_id = client_data.get("_id")
                        break
            
            if not client_id:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Client not found: {mac}")],
                    structured_content={"error": f"Client with MAC {mac} not found"}
                )
            
            data = {"name": name} if name else {"name": ""}
            
            result = await client._make_request("POST", f"/upd/user/{client_id}", 
                                               site_name=site_name, 
                                               data=data)
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )
            
            action = "updated" if name else "removed"
            resp = {
                "success": True,
                "message": f"Client {mac} name {action} successfully",
                "mac": normalized_mac,
                "name": name,
                "details": result
            }
            nice = f"Name {action}: {mac} -> '{name}'" if name else f"Name {action}: {mac}"
            return ToolResult(
                content=[TextContent(type="text", text=nice)],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error setting client name for {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def set_client_note(mac: str, note: str, site_name: str = "default") -> ToolResult:
        """
        Set or update the note for a client.
        
        Args:
            mac: Client MAC address (any format)
            note: Note for the client (empty string to remove)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the note update operation
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # First get the client to find its ID
            clients = await client.get_clients(site_name)
            client_id = None
            
            if isinstance(clients, list):
                for client_data in clients:
                    if client_data.get("mac", "").lower().replace("-", ":").replace(".", ":") == normalized_mac:
                        client_id = client_data.get("_id")
                        break
            
            if not client_id:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Client not found: {mac}")],
                    structured_content={"error": f"Client with MAC {mac} not found"}
                )
            
            data = {"note": note} if note else {"note": ""}
            
            result = await client._make_request("POST", f"/upd/user/{client_id}", 
                                               site_name=site_name, 
                                               data=data)
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )
            
            action = "updated" if note else "removed"
            resp = {
                "success": True,
                "message": f"Client {mac} note {action} successfully",
                "mac": normalized_mac,
                "note": note,
                "details": result
            }
            nice = f"Note {action}: {mac} -> '{note}'" if note else f"Note {action}: {mac}"
            return ToolResult(
                content=[TextContent(type="text", text=nice)],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error setting client note for {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
