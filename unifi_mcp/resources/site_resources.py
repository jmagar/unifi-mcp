"""
Site-related MCP resources for UniFi MCP Server.

Provides structured access to site information and configuration.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_generic_list

logger = logging.getLogger(__name__)


def register_site_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all site-related MCP resources."""
    
    @mcp.resource("unifi://sites")
    async def resource_all_sites():
        """Get all sites with clean formatting."""
        try:
            sites = await client.get_sites()
            
            if isinstance(sites, dict) and "error" in sites:
                return f"Error retrieving sites: {sites['error']}"
            
            if not isinstance(sites, list):
                return "Error: Unexpected response format"
            
            return format_generic_list(sites, "UniFi Controller Sites", ["desc", "name", "role"])
            
        except Exception as e:
            return f"Error retrieving sites: {str(e)}"