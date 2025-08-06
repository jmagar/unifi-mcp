"""
Site-related MCP resources for UniFi MCP Server.

Provides structured access to site information and configuration.
"""

import json
import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient

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
            
            # Filter sites to essential info
            filtered_sites = [{
                "name": site.get("name", "Unknown"),
                "desc": site.get("desc", "No description"),
                "_id": site.get("_id", "Unknown"),
                "role": site.get("role", "Unknown"),
                "num_devices": site.get("num_devices", 0),
                "num_clients": site.get("health", [{}])[0].get("num_user", 0) if site.get("health") else 0,
                "health_status": "OK" if all(h.get("status") == "ok" for h in site.get("health", [])) else "Warning"
            } for site in sites]
            return json.dumps(filtered_sites, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"Error retrieving sites: {str(e)}"