"""
Device management tools for UniFi MCP Server.

Provides tools for listing, managing, and controlling UniFi devices.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..client import UnifiControllerClient
from ..formatters import format_device_summary, format_devices_list

logger = logging.getLogger(__name__)


def register_device_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all device management tools."""
    
    @mcp.tool()
    async def get_devices(site_name: str = "default") -> ToolResult:
        """
        Get all devices with clean, formatted summaries.
        
        Args:
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of devices with formatted, essential information
        """
        try:
            devices = await client.get_devices(site_name)
            
            if isinstance(devices, dict) and "error" in devices:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {devices.get('error','unknown error')}")],
                    structured_content=[devices]
                )
            
            if not isinstance(devices, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content=[{"error": "Unexpected response format"}]
                )
            
            # Format each device for clean output
            formatted_devices = []
            for device in devices:
                try:
                    formatted_device = format_device_summary(device)
                    formatted_devices.append(formatted_device)
                except Exception as e:
                    logger.error(f"Error formatting device {device.get('name', 'Unknown')}: {e}")
                    formatted_devices.append({
                        "name": device.get("name", "Unknown"),
                        "error": f"Formatting error: {str(e)}"
                    })
            
            # Token-efficient human summary
            summary_text = format_devices_list(devices)

            return ToolResult(
                content=[TextContent(type="text", text=summary_text)],
                structured_content=formatted_devices
            )
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content=[{"error": str(e)}]
            )
    
    
    @mcp.tool()
    async def get_device_by_mac(mac: str, site_name: str = "default") -> ToolResult:
        """
        Get specific device details by MAC address with formatted output.
        
        Args:
            mac: Device MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Device details with clean, formatted information
        """
        try:
            devices = await client.get_devices(site_name)
            
            if isinstance(devices, dict) and "error" in devices:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {devices.get('error','unknown error')}")],
                    structured_content=devices
                )
            
            if not isinstance(devices, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format"}
                )
            
            # Normalize MAC address for comparison
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # Find matching device
            for device in devices:
                device_mac = device.get("mac", "").lower().replace("-", ":").replace(".", ":")
                if device_mac == normalized_mac:
                    formatted = format_device_summary(device)
                    lines = [
                        f"Device Details",
                        f"  {formatted.get('name','Unknown')} | {formatted.get('model','Unknown')} ({formatted.get('type','Device')})",
                        f"  Status: {formatted.get('status','Unknown')} | IP: {formatted.get('ip','Unknown')} | Uptime: {formatted.get('uptime','Unknown')}",
                        f"  MAC: {formatted.get('mac','').upper()} | Version: {formatted.get('version','Unknown')}"
                    ]
                    return ToolResult(
                        content=[TextContent(type="text", text="\n".join(lines))],
                        structured_content=formatted
                    )

            return ToolResult(
                content=[TextContent(type="text", text=f"Device with MAC {mac} not found")],
                structured_content={"error": f"Device with MAC {mac} not found"}
            )
            
        except Exception as e:
            logger.error(f"Error getting device by MAC {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def restart_device(mac: str, site_name: str = "default") -> ToolResult:
        """
        Restart a UniFi device.
        
        Args:
            mac: Device MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the restart operation
        """
        try:
            result = await client.restart_device(mac, site_name)
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Device {mac} restart command sent",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Device restart requested: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error restarting device {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
    
    
    @mcp.tool()
    async def locate_device(mac: str, site_name: str = "default") -> ToolResult:
        """
        Trigger locate LED on a UniFi device.
        
        Args:
            mac: Device MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the locate operation
        """
        try:
            result = await client.locate_device(mac, site_name)
            
            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Device {mac} locate LED activated",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Locate LED activated: {mac}")],
                structured_content=resp
            )
            
        except Exception as e:
            logger.error(f"Error locating device {mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )
