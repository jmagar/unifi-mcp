"""
Client service for UniFi MCP Server.

Handles all client management operations including listing, control, and configuration.
"""

import logging
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .base import BaseService
from ..models.enums import UnifiAction
from ..models.params import UnifiParams
from ..formatters import format_client_summary, format_clients_list

logger = logging.getLogger(__name__)


class ClientService(BaseService):
    """Service for client management operations.

    Provides consolidated access to client listing, control, and configuration operations.
    """

    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute client-related actions.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with action response
        """
        action_map = {
            UnifiAction.GET_CLIENTS: self._get_clients,
            UnifiAction.RECONNECT_CLIENT: self._reconnect_client,
            UnifiAction.BLOCK_CLIENT: self._block_client,
            UnifiAction.UNBLOCK_CLIENT: self._unblock_client,
            UnifiAction.FORGET_CLIENT: self._forget_client,
            UnifiAction.SET_CLIENT_NAME: self._set_client_name,
            UnifiAction.SET_CLIENT_NOTE: self._set_client_note,
        }

        handler = action_map.get(params.action)
        if not handler:
            return self.create_error_result(
                f"Client action {params.action} not supported"
            )

        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"Error executing client action {params.action}: {e}")
            return self.create_error_result(str(e))

    async def _get_clients(self, params: UnifiParams) -> ToolResult:
        """Get connected clients with formatted connection details."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            connected_only = params.connected_only if params.connected_only is not None else defaults.get('connected_only', True)

            clients = await self.client.get_clients(site_name)

            # Check for error response
            if isinstance(clients, dict) and "error" in clients:
                return self.create_error_result(clients.get('error','unknown error'), clients)

            if not isinstance(clients, list):
                return self.create_error_result("Unexpected response format")

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
            return self.create_success_result(
                text=summary_text,
                data=formatted_clients,
                success_message=f"Retrieved {len(formatted_clients)} clients"
            )

        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return self.create_error_result(str(e))

    async def _reconnect_client(self, params: UnifiParams) -> ToolResult:
        """Force reconnection of a client device."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            result = await self.client.reconnect_client(params.mac, site_name)

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Client {params.mac} reconnect command sent",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Reconnect requested: {params.mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error reconnecting client {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _block_client(self, params: UnifiParams) -> ToolResult:
        """Block a client from accessing the network."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            result = await self.client._make_request("POST", "/cmd/stamgr",
                                                   site_name=site_name,
                                                   data={"cmd": "block-sta", "mac": normalized_mac})

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Client {normalized_mac} has been blocked from network access",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Blocked client: {normalized_mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error blocking client {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _unblock_client(self, params: UnifiParams) -> ToolResult:
        """Unblock a previously blocked client."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            result = await self.client._make_request("POST", "/cmd/stamgr",
                                                   site_name=site_name,
                                                   data={"cmd": "unblock-sta", "mac": normalized_mac})

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Client {normalized_mac} has been unblocked and can access the network",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Unblocked client: {normalized_mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error unblocking client {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _forget_client(self, params: UnifiParams) -> ToolResult:
        """Remove historical data for a client (GDPR compliance)."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            result = await self.client._make_request("POST", "/cmd/stamgr",
                                                   site_name=site_name,
                                                   data={"cmd": "forget-sta", "macs": [normalized_mac]})

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Client {normalized_mac} historical data has been removed",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Forgot client data: {normalized_mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error forgetting client {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _set_client_name(self, params: UnifiParams) -> ToolResult:
        """Set or update the name/alias for a client."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            # Resolve user id from controller users, not active sessions
            users = await self.client._make_request("GET", "/list/user", site_name=site_name)
            client_id = None
            if isinstance(users, list):
                for u in users:
                    if self.normalize_mac(u.get("mac", "")) == normalized_mac:
                        client_id = u.get("_id") or u.get("user_id")
                        break
            elif isinstance(users, dict) and "error" in users:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {users.get('error','unknown error')}")],
                    structured_content={"error": users.get("error","unknown error"), "raw": users}
                )

            if not client_id:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Client not found: {normalized_mac}")],
                    structured_content={"error": f"Client with MAC {normalized_mac} not found"}
                )

            data = {"name": params.name} if params.name else {"name": ""}

            result = await self.client._make_request("POST", f"/upd/user/{client_id}",
                                                   site_name=site_name,
                                                   data=data)

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            action = "updated" if params.name else "removed"
            resp = {
                "success": True,
                "message": f"Client {normalized_mac} name {action} successfully",
                "mac": normalized_mac,
                "name": params.name,
                "details": result
            }
            nice = f"Name {action}: {normalized_mac} -> '{params.name}'" if params.name else f"Name {action}: {normalized_mac}"
            return ToolResult(
                content=[TextContent(type="text", text=nice)],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error setting client name for {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _set_client_note(self, params: UnifiParams) -> ToolResult:
        """Set or update the note for a client."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            # Resolve user id from controller users, not active sessions
            users = await self.client._make_request("GET", "/list/user", site_name=site_name)
            client_id = None
            if isinstance(users, list):
                for u in users:
                    if self.normalize_mac(u.get("mac", "")) == normalized_mac:
                        client_id = u.get("_id") or u.get("user_id")
                        break
            elif isinstance(users, dict) and "error" in users:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {users.get('error','unknown error')}")],
                    structured_content={"error": users.get("error","unknown error"), "raw": users}
                )

            if not client_id:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Client not found: {normalized_mac}")],
                    structured_content={"error": f"Client with MAC {normalized_mac} not found"}
                )

            data = {"note": params.note} if params.note else {"note": ""}

            result = await self.client._make_request("POST", f"/upd/user/{client_id}",
                                                   site_name=site_name,
                                                   data=data)

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            action = "updated" if params.note else "removed"
            resp = {
                "success": True,
                "message": f"Client {normalized_mac} note {action} successfully",
                "mac": normalized_mac,
                "note": params.note,
                "details": result
            }
            nice = f"Note {action}: {normalized_mac} -> '{params.note}'" if params.note else f"Note {action}: {normalized_mac}"
            return ToolResult(
                content=[TextContent(type="text", text=nice)],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error setting client note for {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )