"""
FastMCP server setup and configuration for UniFi MCP Server.

Handles server initialization, tool and resource registration,
and server lifecycle management.
"""

import logging
import os
from typing import Optional, Annotated
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from .config import UniFiConfig, ServerConfig
from .client import UnifiControllerClient
from .models import UnifiAction, UnifiParams
from .services import UnifiService
from .resources import (
    register_device_resources,
    register_client_resources,
    register_network_resources,
    register_monitoring_resources,
    register_overview_resources,
    register_site_resources
)

logger = logging.getLogger(__name__)


def _normalize_mac(mac: str) -> str:
    return mac.strip().lower().replace("-", ":").replace(".", ":")


class UniFiMCPServer:
    """UniFi MCP Server with modular architecture."""
    
    def __init__(self, unifi_config: UniFiConfig, server_config: ServerConfig):
        """Initialize the UniFi MCP server."""
        self.unifi_config = unifi_config
        self.server_config = server_config
        
        # Check if Google OAuth is configured via environment variables
        auth_provider = os.getenv("FASTMCP_SERVER_AUTH")
        self._auth_enabled = False
        
        if auth_provider in ["google", "fastmcp.server.auth.providers.google.GoogleProvider"]:
            logger.info("Google OAuth authentication requested")
            # Validate required Google env vars
            client_id = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID")
            client_secret = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET")
            base_url = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL")
            
            if not client_id or not client_secret or not base_url:
                logger.error("Missing required Google OAuth environment variables")
                logger.error("Required: FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID, FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET, FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL")
                self.mcp = FastMCP("UniFi Local Controller MCP Server")
            else:
                try:
                    from fastmcp.server.auth.providers.google import GoogleProvider
                    
                    # Build scopes by splitting and filtering
                    scopes_str = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES", "")
                    if scopes_str:
                        scopes = [s.strip() for s in scopes_str.split(",") if s.strip()]
                    else:
                        scopes = []
                    
                    if not scopes:
                        scopes = ["openid", "email", "profile"]
                    
                    google_provider = GoogleProvider(
                        client_id=client_id,
                        client_secret=client_secret,
                        base_url=base_url,
                        required_scopes=scopes,
                        redirect_path=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_REDIRECT_PATH", "/auth/callback"),
                        timeout_seconds=int(os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_TIMEOUT_SECONDS", "10"))
                    )
                    
                    self.mcp = FastMCP("UniFi Local Controller MCP Server", auth=google_provider)
                    self._auth_enabled = True
                    logger.info("Google OAuth provider configured successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to configure Google OAuth: {e}")
                    logger.info("Falling back to no authentication")
                    self.mcp = FastMCP("UniFi Local Controller MCP Server")
        else:
            logger.info("No authentication configured - server will run without OAuth")
            self.mcp = FastMCP("UniFi Local Controller MCP Server")
        self.client: Optional[UnifiControllerClient] = None
        self.unifi_service: Optional[UnifiService] = None
        
    async def initialize(self) -> None:
        """Initialize the UniFi client and register tools/resources."""
        logger.info("Initializing UniFi MCP Server...")
        
        # Initialize UniFi client
        self.client = UnifiControllerClient(self.unifi_config)
        try:
            await self.client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to UniFi controller: {e}")
            # Optionally: raise to abort startup
            raise

        # Initialize unified service
        self.unifi_service = UnifiService(self.client)

        # Register unified tool
        logger.info("Registering unified MCP tool...")
        self._register_unified_tool()
        
        # Note: Authentication test tool (get_user_info) is now handled by the unified tool
        
        # Register all resources
        logger.info("Registering MCP resources...")
        register_device_resources(self.mcp, self.client)
        register_client_resources(self.mcp, self.client)
        register_network_resources(self.mcp, self.client)
        register_monitoring_resources(self.mcp, self.client)
        register_overview_resources(self.mcp, self.client)
        register_site_resources(self.mcp, self.client)
        
        logger.info("UniFi MCP Server initialization complete")
    
    def _register_unified_tool(self) -> None:
        """Register the unified UniFi tool that handles all actions."""
        logger.info("Registering unified UniFi tool...")

        @self.mcp.tool()
        async def unifi(
            action: Annotated[str, Field(description="The action to perform. See UnifiAction enum for all available actions.")],
            site_name: Annotated[str, Field(default="default", description="UniFi site name (not used by get_sites, get_controller_status, get_user_info)")] = "default",
            mac: Annotated[Optional[str], Field(default=None, description="Device or client MAC address (any format, required for device/client operations)")] = None,
            limit: Annotated[Optional[int], Field(default=None, description="Maximum number of results to return (default varies by action)")] = None,
            connected_only: Annotated[Optional[bool], Field(default=None, description="Only return currently connected clients (get_clients only, default: True)")] = None,
            active_only: Annotated[Optional[bool], Field(default=None, description="Only return active/unarchived items (get_alarms only, default: True)")] = None,
            by_filter: Annotated[Optional[str], Field(default=None, description="Filter type for DPI stats: 'by_app' or 'by_cat' (get_dpi_stats only, default: 'by_app')")] = None,
            name: Annotated[Optional[str], Field(default=None, description="New name for client (set_client_name only)")] = None,
            note: Annotated[Optional[str], Field(default=None, description="Note for client (set_client_note only)")] = None,
            minutes: Annotated[Optional[int], Field(default=None, description="Duration of guest access in minutes (authorize_guest only, default: 480 = 8 hours)")] = None,
            up_bandwidth: Annotated[Optional[int], Field(default=None, description="Upload bandwidth limit in Kbps (authorize_guest only)")] = None,
            down_bandwidth: Annotated[Optional[int], Field(default=None, description="Download bandwidth limit in Kbps (authorize_guest only)")] = None,
            quota: Annotated[Optional[int], Field(default=None, description="Data quota in MB (authorize_guest only)")] = None,
        ) -> ToolResult:
            """Unified UniFi tool providing access to all device, client, network, and monitoring operations.

            This consolidated tool replaces 31 individual tools with a single action-based interface.
            All previous functionality is preserved while providing better type safety and efficiency.

            Available Actions:
            - Device Management: get_devices, get_device_by_mac, restart_device, locate_device
            - Client Management: get_clients, reconnect_client, block_client, unblock_client, forget_client, set_client_name, set_client_note
            - Network Configuration: get_sites, get_wlan_configs, get_network_configs, get_port_configs, get_port_forwarding_rules, get_firewall_rules, get_firewall_groups, get_static_routes
            - Monitoring & Statistics: get_controller_status, get_events, get_alarms, get_dpi_stats, get_rogue_aps, start_spectrum_scan, get_spectrum_scan_state, authorize_guest, get_speedtest_results, get_ips_events
            - Authentication: get_user_info

            Args:
                action: The action to perform (see above for available actions)
                site_name: UniFi site name (default: "default")
                mac: Device or client MAC address (required for device/client operations)
                limit: Maximum number of results to return
                connected_only: Only return currently connected clients (get_clients)
                active_only: Only return active/unarchived items (get_alarms)
                by_filter: Filter type for DPI stats: 'by_app' or 'by_cat' (get_dpi_stats)
                name: New name for client (set_client_name)
                note: Note for client (set_client_note)
                minutes: Duration of guest access in minutes (authorize_guest)
                up_bandwidth: Upload bandwidth limit in Kbps (authorize_guest)
                down_bandwidth: Download bandwidth limit in Kbps (authorize_guest)
                quota: Data quota in MB (authorize_guest)

            Returns:
                ToolResult with action response and structured data
            """
            try:
                # Parse and validate action
                try:
                    unifi_action = UnifiAction(action)
                except ValueError:
                    available_actions = [action.value for action in UnifiAction]
                    return ToolResult(
                        content=[{
                            "type": "text",
                            "text": f"Invalid action '{action}'. Available actions: {', '.join(available_actions)}"
                        }],
                        structured_content={"error": f"Invalid action: {action}", "available_actions": available_actions}
                    )

                # Create and validate parameters
                params = UnifiParams(
                    action=unifi_action,
                    site_name=site_name,
                    mac=mac,
                    limit=limit,
                    connected_only=connected_only,
                    active_only=active_only,
                    by_filter=by_filter,
                    name=name,
                    note=note,
                    minutes=minutes,
                    up_bandwidth=up_bandwidth,
                    down_bandwidth=down_bandwidth,
                    quota=quota
                )

                # Execute action through service layer
                if not self.unifi_service:
                    return ToolResult(
                        content=[{"type": "text", "text": "Error: Service not initialized"}],
                        structured_content={"error": "Service not initialized"}
                    )
                return await self.unifi_service.execute_action(params)

            except Exception as e:
                logger.error(f"Error in unified UniFi tool: {e}")
                return ToolResult(
                    content=[{"type": "text", "text": f"Error: {str(e)}"}],
                    structured_content={"error": str(e)}
                )

        logger.info("Unified UniFi tool registered successfully")
    
    async def cleanup(self) -> None:
        """Cleanup server resources."""
        logger.info("Cleaning up UniFi MCP Server...")
        
        if self.client:
            await self.client.disconnect()
            
        logger.info("UniFi MCP Server cleanup complete")
    
    def get_app(self):
        """Get the FastMCP application instance."""
        return self.mcp.http_app
    
    async def run(self) -> None:
        """Run the server (for standalone execution)."""
        import uvicorn
        
        await self.initialize()
        
        try:
            app = self.get_app()
            config = uvicorn.Config(
                app,
                host=self.server_config.host,
                port=self.server_config.port,
                log_level=self.server_config.log_level.lower()
            )
            server = uvicorn.Server(config)
            
            logger.info(f"Starting UniFi MCP Server on {self.server_config.host}:{self.server_config.port}")
            await server.serve()
            
        finally:
            await self.cleanup()