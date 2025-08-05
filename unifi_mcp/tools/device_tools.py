"""
Device management tools for UniFi MCP Server.

Provides tools for listing, managing, and controlling UniFi devices.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_device_summary

logger = logging.getLogger(__name__)


def register_device_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all device management tools."""
    
    @mcp.tool()
    async def get_devices(site_name: str = "default") -> List[Dict[str, Any]]:
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
                return [devices]
            
            if not isinstance(devices, list):
                return [{"error": "Unexpected response format"}]
            
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
            
            return formatted_devices
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_device_by_mac(mac: str, site_name: str = "default") -> Dict[str, Any]:
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
                return devices
            
            if not isinstance(devices, list):
                return {"error": "Unexpected response format"}
            
            # Normalize MAC address for comparison
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            # Find matching device
            for device in devices:
                device_mac = device.get("mac", "").lower().replace("-", ":").replace(".", ":")
                if device_mac == normalized_mac:
                    return format_device_summary(device)
            
            return {"error": f"Device with MAC {mac} not found"}
            
        except Exception as e:
            logger.error(f"Error getting device by MAC {mac}: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def restart_device(mac: str, site_name: str = "default") -> Dict[str, Any]:
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
                return result
            
            return {
                "success": True,
                "message": f"Device {mac} restart command sent",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error restarting device {mac}: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def locate_device(mac: str, site_name: str = "default") -> Dict[str, Any]:
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
                return result
            
            return {
                "success": True,
                "message": f"Device {mac} locate LED activated",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error locating device {mac}: {e}")
            return {"error": str(e)}