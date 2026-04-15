"""
Base service for UniFi MCP Server service layer.

Provides shared functionality and common patterns for all domain services.
"""

import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import cast

from fastmcp.tools.base import ToolResult
from mcp.types import TextContent

from ..client import UnifiControllerClient
from ..models.enums import UnifiAction
from ..models.params import UnifiParams
from ..types import ErrorResponse, JSONValue, UniFiData

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base service providing shared functionality for all domain services.

    This class centralizes common patterns like MAC address normalization,
    error handling, and ToolResult construction.
    """

    def __init__(self, client: UnifiControllerClient):
        """Initialize the base service.

        Args:
            client: UniFi controller client for API operations
        """
        self.client = client

    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normalize MAC address to consistent format.

        Converts any MAC address format to lowercase colon-separated format.
        Validates the MAC address format.

        Args:
            mac: MAC address in any format (xx:xx:xx:xx:xx:xx, xx-xx-xx-xx-xx-xx, etc.)

        Returns:
            Normalized MAC address in xx:xx:xx:xx:xx:xx format

        Raises:
            ValueError: If the MAC address format is invalid
        """
        # Normalize to colon-separated format
        normalized = mac.strip().lower().replace("-", ":").replace(".", ":")

        # Validate MAC address format (6 groups of 2 hex digits)
        if not re.match(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", normalized):
            raise ValueError(f"Invalid MAC address format: {mac}")

        return normalized

    @staticmethod
    def create_error_result(message: str, raw_data: UniFiData | ErrorResponse | dict[str, JSONValue] | None = None) -> ToolResult:
        """Create standardized error ToolResult.

        Args:
            message: Human-readable error message
            raw_data: Optional raw data to include in structured content

        Returns:
            ToolResult with error information
        """
        return ToolResult(content=[TextContent(type="text", text=f"Error: {message}")], structured_content={"error": message, "raw": raw_data})

    @staticmethod
    def create_success_result(
        text: str, data: UniFiData | dict[str, JSONValue] | list[dict[str, JSONValue]] | JSONValue, success_message: str | None = None
    ) -> ToolResult:
        """Create standardized success ToolResult.

        Args:
            text: Human-readable text content
            data: Structured data content
            success_message: Optional success message for structured content

        Returns:
            ToolResult with success information
        """
        structured_content: dict[str, JSONValue] | UniFiData | list[dict[str, JSONValue]] | JSONValue = data
        if success_message and isinstance(data, dict):
            # Build dict with update() to avoid TypedDict unpacking issues
            structured_content = cast("dict[str, JSONValue]", {"success": True, "message": success_message})
            structured_content.update(cast("dict[str, JSONValue]", data))
        elif success_message:
            structured_content = {"success": True, "message": success_message, "data": cast("JSONValue", data)}

        return ToolResult(content=[TextContent(type="text", text=text)], structured_content=structured_content)

    def validate_response(self, response: UniFiData | ErrorResponse | dict[str, JSONValue], action: UnifiAction) -> tuple[bool, str]:
        """Validate API response for common error patterns.

        Args:
            response: API response to validate
            action: Action that generated the response

        Returns:
            Tuple of (is_valid, error_message)
        """
        if isinstance(response, dict):
            if "error" in response:
                error_val = response.get("error", "unknown error")
                return False, str(error_val) if error_val is not None else "unknown error"

            # Check UniFi API response code
            meta = response.get("meta", {})
            if isinstance(meta, dict):
                rc = meta.get("rc")
                if rc and rc != "ok":
                    msg = meta.get("msg", "Controller returned failure")
                    return False, str(msg) if msg is not None else "Controller returned failure"

        return True, ""

    def check_list_response(self, response: UniFiData | ErrorResponse | dict[str, JSONValue], action: UnifiAction) -> ToolResult | None:
        """Check if response is a valid list and handle common error cases.

        Args:
            response: API response to check
            action: Action that generated the response

        Returns:
            ToolResult if there's an error, None if response is valid
        """
        # Check for error dict
        if isinstance(response, dict) and "error" in response:
            error_val = response.get("error", "unknown error")
            return self.create_error_result(str(error_val) if error_val is not None else "unknown error", response)

        # Check if response is expected list format
        if not isinstance(response, list):
            error_msg = f"Unexpected response format: expected list, got {type(response).__name__}"
            return self.create_error_result(error_msg, None)

        return None

    def format_action_result(
        self,
        response: UniFiData | ErrorResponse | dict[str, JSONValue],
        action: UnifiAction,
        formatter_func: Callable[[UniFiData | dict[str, JSONValue]], dict[str, JSONValue] | list[dict[str, JSONValue]] | str] | None = None,
        success_text: str | None = None,
    ) -> ToolResult:
        """Format action result with consistent error handling.

        Args:
            response: API response to format
            action: Action that generated the response
            formatter_func: Optional function to format the response
            success_text: Optional success text override

        Returns:
            Formatted ToolResult
        """
        # Validate response
        is_valid, error_msg = self.validate_response(response, action)
        if not is_valid:
            return self.create_error_result(error_msg, response)

        # Format response if formatter provided
        if formatter_func:
            try:
                formatted_data = formatter_func(cast("UniFiData | dict[str, JSONValue]", response))
                text = success_text or f"{action.value} completed successfully"
                return self.create_success_result(text, formatted_data)
            except Exception as e:
                logger.error(f"Error formatting response for {action.value}: {e}")
                return self.create_error_result(f"Formatting error: {e!s}", response)

        # Return raw response if no formatter
        text = success_text or f"{action.value} completed"
        return self.create_success_result(text, cast("UniFiData | dict[str, JSONValue] | list[dict[str, JSONValue]] | JSONValue", response))

    @abstractmethod
    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute the specified action with the given parameters.

        This is the main entry point that subclasses must override
        to implement their specific action routing.

        Args:
            params: Validated parameters for the action

        Returns:
            ToolResult with action response
        """
