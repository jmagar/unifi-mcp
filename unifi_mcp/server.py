"""
FastMCP server setup and configuration for UniFi MCP Server.

Handles server initialization, tool and resource registration,
and server lifecycle management.
"""

import logging
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
    register_overview_resources
)

logger = logging.getLogger(__name__)


class UniFiMCPServer:
    """UniFi MCP Server with modular architecture."""
    
    def __init__(self, unifi_config: UniFiConfig, server_config: ServerConfig):
        """Initialize the UniFi MCP server."""
        self.unifi_config = unifi_config
        self.server_config = server_config
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
        
        # Register all resources
        logger.info("Registering MCP resources...")
        register_device_resources(self.mcp, self.client)
        register_client_resources(self.mcp, self.client)
        register_network_resources(self.mcp, self.client)
        register_monitoring_resources(self.mcp, self.client)
        register_overview_resources(self.mcp, self.client)
        
        logger.info("UniFi MCP Server initialization complete")
    
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