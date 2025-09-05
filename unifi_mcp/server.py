"""
FastMCP server setup and configuration for UniFi MCP Server.

Handles server initialization, tool and resource registration,
and server lifecycle management.
"""

import logging
import os
from typing import Optional
from fastmcp import FastMCP

from .config import UniFiConfig, ServerConfig
from .client import UnifiControllerClient
from .tools import (
    register_device_tools,
    register_client_tools,
    register_network_tools,
    register_monitoring_tools
)
from .resources import (
    register_device_resources,
    register_client_resources,
    register_network_resources,
    register_monitoring_resources,
    register_overview_resources,
    register_site_resources
)

logger = logging.getLogger(__name__)


class UniFiMCPServer:
    """UniFi MCP Server with modular architecture."""
    
    def __init__(self, unifi_config: UniFiConfig, server_config: ServerConfig):
        """Initialize the UniFi MCP server."""
        self.unifi_config = unifi_config
        self.server_config = server_config
        
        # Check if OAuth is configured via environment variables
        auth_provider = os.getenv("FASTMCP_SERVER_AUTH")
        if auth_provider:
            logger.info(f"OAuth authentication enabled: {auth_provider}")
            # Manually create GoogleProvider with environment variables
            try:
                from fastmcp.server.auth.providers.google import GoogleProvider
                
                google_provider = GoogleProvider(
                    client_id=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID"),
                    client_secret=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET"),
                    base_url=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL"),
                    required_scopes=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES", "").split(","),
                    redirect_path=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_REDIRECT_PATH", "/auth/callback"),
                    timeout_seconds=int(os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_TIMEOUT_SECONDS", "10"))
                )
                
                self.mcp = FastMCP("UniFi Local Controller MCP Server", auth=google_provider)
                logger.info("Google OAuth provider configured successfully")
                
            except Exception as e:
                logger.error(f"Failed to configure Google OAuth: {e}")
                logger.info("Falling back to no authentication")
                self.mcp = FastMCP("UniFi Local Controller MCP Server")
        else:
            logger.info("No authentication configured - server will run without OAuth")
            self.mcp = FastMCP("UniFi Local Controller MCP Server")
        self.client: Optional[UnifiControllerClient] = None
        
    async def initialize(self) -> None:
        """Initialize the UniFi client and register tools/resources."""
        logger.info("Initializing UniFi MCP Server...")
        
        # Initialize UniFi client
        self.client = UnifiControllerClient(self.unifi_config)
        await self.client.connect()
        
        # Register all tools
        logger.info("Registering MCP tools...")
        register_device_tools(self.mcp, self.client)
        register_client_tools(self.mcp, self.client)
        register_network_tools(self.mcp, self.client)
        register_monitoring_tools(self.mcp, self.client)
        
        # Register authentication test tool if OAuth is enabled
        if os.getenv("FASTMCP_SERVER_AUTH"):
            self._register_auth_tools()
        
        # Register all resources
        logger.info("Registering MCP resources...")
        register_device_resources(self.mcp, self.client)
        register_client_resources(self.mcp, self.client)
        register_network_resources(self.mcp, self.client)
        register_monitoring_resources(self.mcp, self.client)
        register_overview_resources(self.mcp, self.client)
        register_site_resources(self.mcp, self.client)
        
        logger.info("UniFi MCP Server initialization complete")
    
    def _register_auth_tools(self) -> None:
        """Register authentication-related tools for testing OAuth."""
        logger.info("Registering authentication test tools...")
        
        @self.mcp.tool
        async def get_user_info() -> dict:
            """Returns information about the authenticated Google user.
            
            This tool requires Google OAuth authentication and can be used to test
            that the authentication system is working properly.
            
            Returns:
                dict: User information including email, name, Google ID, etc.
            """
            try:
                # Import here to avoid issues if not using authentication
                from fastmcp.server.dependencies import get_access_token
                
                token = get_access_token()
                # The GoogleProvider stores user data in token claims
                user_info = {
                    "google_id": token.claims.get("sub"),
                    "email": token.claims.get("email"),
                    "name": token.claims.get("name"),
                    "picture": token.claims.get("picture"),
                    "locale": token.claims.get("locale"),
                    "verified_email": token.claims.get("email_verified"),
                    "token_issued_at": token.claims.get("iat"),
                    "token_expires_at": token.claims.get("exp")
                }
                
                logger.info(f"User authenticated: {user_info.get('email', 'unknown')}")
                return user_info
                
            except Exception as e:
                logger.error(f"Error getting user info: {e}")
                return {
                    "error": f"Failed to get user info: {str(e)}",
                    "authenticated": False
                }
        
        logger.info("Authentication test tools registered successfully")
    
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