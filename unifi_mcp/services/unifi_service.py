"""
UniFi service coordinator for the consolidated tool interface.

Routes actions to appropriate domain services and handles authentication.
"""

import logging
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .base import BaseService
from .device_service import DeviceService
from .client_service import ClientService
from .network_service import NetworkService
from .monitoring_service import MonitoringService
from ..client import UnifiControllerClient
from ..models.enums import (
    UnifiAction,
    DEVICE_ACTIONS,
    CLIENT_ACTIONS,
    NETWORK_ACTIONS,
    MONITORING_ACTIONS,
    AUTH_ACTIONS
)
from ..models.params import UnifiParams

logger = logging.getLogger(__name__)


class UnifiService:
    """Main service coordinator for the unified UniFi tool.

    Routes actions to appropriate domain services while maintaining
    a clean separation of concerns.
    """

    def __init__(self, client: UnifiControllerClient):
        """Initialize the UniFi service coordinator.

        Args:
            client: UniFi controller client for API operations
        """
        self.client = client

        # Initialize domain services
        self.device_service = DeviceService(client)
        self.client_service = ClientService(client)
        self.network_service = NetworkService(client)
        self.monitoring_service = MonitoringService(client)

    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute the specified action by routing to the appropriate service.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with action response
        """
        try:
            # Route to appropriate domain service
            if params.action in DEVICE_ACTIONS:
                return await self.device_service.execute_action(params)
            elif params.action in CLIENT_ACTIONS:
                return await self.client_service.execute_action(params)
            elif params.action in NETWORK_ACTIONS:
                return await self.network_service.execute_action(params)
            elif params.action in MONITORING_ACTIONS:
                return await self.monitoring_service.execute_action(params)
            elif params.action in AUTH_ACTIONS:
                return await self._handle_auth_action(params)
            else:
                return self._create_error_result(
                    f"Unknown action: {params.action}"
                )

        except Exception as e:
            logger.error(f"Error executing action {params.action}: {e}")
            return self._create_error_result(str(e))

    async def _handle_auth_action(self, params: UnifiParams) -> ToolResult:
        """Handle authentication-related actions.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with authentication response
        """
        if params.action == UnifiAction.GET_USER_INFO:
            return await self._get_user_info()
        else:
            return self._create_error_result(
                f"Authentication action {params.action} not supported"
            )

    async def _get_user_info(self) -> ToolResult:
        """Get authenticated user information (OAuth only).

        Returns:
            ToolResult with user information or error if OAuth not enabled
        """
        try:
            # Import here to avoid issues if not using authentication
            from fastmcp.server.dependencies import get_access_token
            from datetime import datetime, timezone

            def _to_iso(ts):
                try:
                    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
                except Exception:
                    return ts

            token = get_access_token()
            # If get_access_token becomes async in future versions:
            # token = await get_access_token()
            # The GoogleProvider stores user data in token claims
            user_info = {
                "google_id": token.claims.get("sub"),
                "email": token.claims.get("email"),
                "name": token.claims.get("name"),
                "picture": token.claims.get("picture"),
                "locale": token.claims.get("locale"),
                "verified_email": token.claims.get("email_verified"),
                "token_issued_at": _to_iso(token.claims.get("iat")),
                "token_expires_at": _to_iso(token.claims.get("exp")),
                "authenticated": True,
            }

            logger.debug("User authenticated.")
            return ToolResult(
                content=[TextContent(type="text", text=f"Authenticated as: {user_info.get('email', 'Unknown')}")],
                structured_content=user_info
            )

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={
                    "error": f"Failed to get user info: {str(e)}",
                    "authenticated": False
                }
            )

    @staticmethod
    def _create_error_result(message: str, raw_data=None) -> ToolResult:
        """Create standardized error ToolResult.

        Args:
            message: Human-readable error message
            raw_data: Optional raw data to include

        Returns:
            ToolResult with error information
        """
        return ToolResult(
            content=[TextContent(type="text", text=f"Error: {message}")],
            structured_content={"error": message, "raw": raw_data}
        )