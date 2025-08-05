"""
Main entry point for the modular UniFi MCP Server.

This module provides the main execution entry point and can be used
to run the server directly or imported for integration.
"""

import asyncio
import logging
import sys
from typing import Optional

from .config import load_config, setup_logging
from .server import UniFiMCPServer

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for the UniFi MCP Server."""
    server: Optional[UniFiMCPServer] = None
    
    try:
        # Load configuration
        unifi_config, server_config = load_config()
        
        # Setup logging
        setup_logging(server_config)
        
        logger.info("Starting UniFi MCP Server (modular version)")
        logger.info(f"Controller URL: {unifi_config.controller_url}")
        logger.info(f"Server: {server_config.host}:{server_config.port}")
        
        # Create and run server
        server = UniFiMCPServer(unifi_config, server_config)
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if server:
            await server.cleanup()
        logger.info("UniFi MCP Server shutdown complete")


def create_app():
    """Create FastMCP app for ASGI deployment."""
    try:
        # Load configuration
        unifi_config, server_config = load_config()
        
        # Setup logging
        setup_logging(server_config)
        
        # Create server instance
        server = UniFiMCPServer(unifi_config, server_config)
        
        # Initialize server in the background
        asyncio.create_task(server.initialize())
        
        return server.get_app()
        
    except Exception as e:
        logger.error(f"Failed to create app: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())