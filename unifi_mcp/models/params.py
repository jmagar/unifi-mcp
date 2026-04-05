"""
Parameter models for UniFi MCP Server unified tool interface.

Defines parameter validation and types for the consolidated unifi tool.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    DESTRUCTIVE_ACTIONS,
    MAC_REQUIRED_ACTIONS,
    NO_SITE_ACTIONS,
    UnifiAction,
)


class UnifiParams(BaseModel):
    """Unified parameter model for all UniFi actions.

    This model handles parameter validation for all 31 actions while
    maintaining type safety and providing clear field descriptions.
    """

    # Core parameters
    action: UnifiAction = Field(..., description="The action to perform")

    site_name: str = Field(
        default="default",
        description="UniFi site name (not used by get_sites, get_controller_status, get_user_info)",
    )

    # Device and client identification
    mac: str | None = Field(default=None, description="Device or client MAC address (any format)")

    # Filtering and limits
    limit: int | None = Field(
        default=None,
        description="Maximum number of results to return (default varies by action)",
    )

    connected_only: bool | None = Field(
        default=None,
        description="Only return currently connected clients (get_clients only, default: True)",
    )

    active_only: bool | None = Field(
        default=None,
        description="Only return active/unarchived items (get_alarms only, default: True)",
    )

    by_filter: str | None = Field(
        default=None,
        description="Filter type for DPI stats: 'by_app' or 'by_cat' (get_dpi_stats only, default: 'by_app')",
    )

    # Client management
    name: str | None = Field(default=None, description="New name for client (set_client_name only)")

    note: str | None = Field(default=None, description="Note for client (set_client_note only)")

    # Guest authorization parameters
    minutes: int | None = Field(
        default=None,
        description="Duration of guest access in minutes (authorize_guest only, default: 480 = 8 hours)",
    )

    up_bandwidth: int | None = Field(
        default=None,
        description="Upload bandwidth limit in Kbps (authorize_guest only)",
    )

    down_bandwidth: int | None = Field(
        default=None,
        description="Download bandwidth limit in Kbps (authorize_guest only)",
    )

    quota: int | None = Field(default=None, description="Data quota in MB (authorize_guest only)")

    # Destructive operation gate
    confirm: bool | None = Field(
        default=None,
        description=(
            "Set to true to confirm destructive operations "
            "(restart_device, block_client, forget_client, reconnect_client). "
            "Bypass via UNIFI_MCP_ALLOW_DESTRUCTIVE=true or "
            "UNIFI_MCP_ALLOW_YOLO=true env vars."
        ),
    )

    @field_validator("up_bandwidth", "down_bandwidth", "quota")
    @classmethod
    def validate_non_negative(cls, v: int | None) -> int | None:
        """Validate that bandwidth and quota are non-negative."""
        if v is not None and v < 0:
            raise ValueError("bandwidth and quota values must be non-negative")
        return v

    @field_validator("limit")
    @classmethod
    def validate_limit_positive(cls, v: int | None) -> int | None:
        """Validate that limit is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("limit must be positive")
        return v

    @field_validator("minutes")
    @classmethod
    def validate_minutes_positive(cls, v: int | None) -> int | None:
        """Validate that minutes is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("minutes must be positive")
        return v

    @field_validator("by_filter")
    @classmethod
    def validate_by_filter_values(cls, v: str | None) -> str | None:
        """Validate by_filter has correct values."""
        if v is not None and v not in ["by_app", "by_cat"]:
            raise ValueError("by_filter must be 'by_app' or 'by_cat'")
        return v

    @model_validator(mode="after")
    def validate_action_requirements(self):
        """Validate cross-field requirements based on action."""
        # Validate MAC address requirement
        if self.action in MAC_REQUIRED_ACTIONS and not self.mac:
            raise ValueError(f"MAC address is required for action: {self.action}")

        # Validate name requirement for set_client_name
        if self.action == UnifiAction.SET_CLIENT_NAME and self.name is None:
            raise ValueError("name parameter is required for set_client_name action")

        # Validate note requirement for set_client_note
        if self.action == UnifiAction.SET_CLIENT_NOTE and self.note is None:
            raise ValueError("note parameter is required for set_client_note action")

        # Validate by_filter requirement for get_dpi_stats
        if self.action == UnifiAction.GET_DPI_STATS and self.by_filter is not None and self.by_filter not in ["by_app", "by_cat"]:
            raise ValueError("by_filter must be 'by_app' or 'by_cat' for get_dpi_stats action")

        # Validate minutes requirement for authorize_guest
        if self.action == UnifiAction.AUTHORIZE_GUEST and self.minutes is not None and self.minutes <= 0:
            raise ValueError("minutes must be positive for authorize_guest action")

        # Note: destructive action gate is enforced at service layer (not here)
        # so that UNIFI_MCP_ALLOW_DESTRUCTIVE / UNIFI_MCP_ALLOW_YOLO env vars
        # can bypass it.
        # DESTRUCTIVE_ACTIONS is referenced here to keep the import alive.
        _ = DESTRUCTIVE_ACTIONS

        return self

    def get_action_defaults(self) -> dict[str, Any]:
        """Get default parameter values for the specific action."""
        defaults: dict[str, Any] = {}

        # Set action-specific defaults
        if self.action == UnifiAction.GET_CLIENTS:
            defaults["connected_only"] = True
        elif self.action == UnifiAction.GET_ALARMS:
            defaults["active_only"] = True
        elif self.action == UnifiAction.GET_DPI_STATS:
            defaults["by_filter"] = "by_app"
        elif self.action == UnifiAction.AUTHORIZE_GUEST:
            defaults["minutes"] = 480
        elif self.action == UnifiAction.GET_EVENTS:
            defaults["limit"] = 100
        elif self.action == UnifiAction.GET_ROGUE_APS or self.action == UnifiAction.GET_SPEEDTEST_RESULTS:
            defaults["limit"] = 20
        elif self.action == UnifiAction.GET_IPS_EVENTS:
            defaults["limit"] = 50

        # Handle site_name special cases
        if self.action not in NO_SITE_ACTIONS:
            defaults["site_name"] = self.site_name or "default"

        return defaults
