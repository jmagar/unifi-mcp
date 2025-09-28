"""
Device service for UniFi MCP Server.

Handles all device management operations including listing, control, and monitoring.
"""

import logging
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .base import BaseService
from ..models.enums import UnifiAction
from ..models.params import UnifiParams
from ..formatters import format_device_summary, format_devices_list

logger = logging.getLogger(__name__)


class DeviceService(BaseService):
    """Service for device management operations.

    Provides consolidated access to device listing, identification,
    and control operations.
    """

    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute device-related actions.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with action response
        """
        action_map = {
            UnifiAction.GET_DEVICES: self._get_devices,
            UnifiAction.GET_DEVICE_BY_MAC: self._get_device_by_mac,
            UnifiAction.RESTART_DEVICE: self._restart_device,
            UnifiAction.LOCATE_DEVICE: self._locate_device,
        }

        handler = action_map.get(params.action)
        if not handler:
            return self.create_error_result(
                f"Device action {params.action} not supported"
            )

        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"Error executing device action {params.action}: {e}")
            return self.create_error_result(str(e))

    async def _get_devices(self, params: UnifiParams) -> ToolResult:
        """Get all devices with clean, formatted summaries."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            devices = await self.client.get_devices(site_name)

            # Check for error response
            error_result = self.check_list_response(devices, params.action)
            if error_result:
                return error_result

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

            return self.create_success_result(
                text=summary_text,
                data=formatted_devices,
                success_message=f"Retrieved {len(formatted_devices)} devices"
            )

        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return self.create_error_result(str(e))

    async def _get_device_by_mac(self, params: UnifiParams) -> ToolResult:
        """Get specific device details by MAC address with formatted output."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            devices = await self.client.get_devices(site_name)

            # Check for error response
            error_result = self.check_list_response(devices, params.action)
            if error_result:
                return error_result

            # Normalize MAC address for comparison
            normalized_mac = self.normalize_mac(params.mac)

            # Find matching device
            for device in devices:
                device_mac = self.normalize_mac(device.get("mac", ""))
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

            return self.create_error_result(f"Device with MAC {params.mac} not found")

        except Exception as e:
            logger.error(f"Error getting device by MAC {params.mac}: {e}")
            return self.create_error_result(str(e))

    async def _restart_device(self, params: UnifiParams) -> ToolResult:
        """Restart a UniFi device."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            result = await self.client.restart_device(params.mac, site_name)

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Device {params.mac} restart command sent",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Device restart requested: {params.mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error restarting device {params.mac}: {e}")
            return self.create_error_result(str(e))

    async def _locate_device(self, params: UnifiParams) -> ToolResult:
        """Trigger locate LED on a UniFi device."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            result = await self.client.locate_device(params.mac, site_name)

            # Check for error in response
            if isinstance(result, dict) and "error" in result:
                return self.create_error_result(result.get('error','unknown error'), result)

            # Validate response
            is_valid, error_msg = self.validate_response(result, params.action)
            if not is_valid:
                return self.create_error_result(error_msg, result)

            resp = {
                "success": True,
                "message": f"Device {params.mac} locate LED activated",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Locate LED activated: {params.mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error locating device {params.mac}: {e}")
            return self.create_error_result(str(e))