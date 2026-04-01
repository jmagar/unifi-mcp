"""
FastMCP server setup and configuration for UniFi MCP Server.

Handles server initialization, tool and resource registration,
and server lifecycle management.
"""

import logging
import os
from datetime import datetime, timezone
from hmac import compare_digest
from typing import Annotated, Optional

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import Field
from mcp.types import TextContent

from .client import UnifiControllerClient
from .config import ServerConfig, UniFiConfig, validate_auth_config
from .models import UnifiAction, UnifiParams
from .models.enums import DESTRUCTIVE_ACTIONS
from .resources import (
    register_client_resources,
    register_device_resources,
    register_monitoring_resources,
    register_network_resources,
    register_overview_resources,
    register_site_resources,
)
from .services import UnifiService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response size cap (512 KB)
# ---------------------------------------------------------------------------
MAX_RESPONSE_SIZE = 512 * 1024  # bytes


def _truncate_response(text: str) -> str:
    """Truncate response text if it exceeds MAX_RESPONSE_SIZE."""
    if len(text.encode("utf-8")) > MAX_RESPONSE_SIZE:
        # Slice by character count — close enough for UTF-8 heavy text
        truncated = text.encode("utf-8")[:MAX_RESPONSE_SIZE].decode(
            "utf-8", errors="ignore"
        )
        return truncated + "\n... [truncated]"
    return text


def _normalize_mac(mac: str) -> str:
    return mac.strip().lower().replace("-", ":").replace(".", ":")


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------


class UniFiMCPServer:
    """UniFi MCP Server with modular architecture."""

    def __init__(self, unifi_config: UniFiConfig, server_config: ServerConfig):
        """Initialize the UniFi MCP server."""
        self.unifi_config = unifi_config
        self.server_config = server_config

        # Validate Bearer token at startup (exits if missing and NO_AUTH != true)
        self._bearer_token: Optional[str] = validate_auth_config()

        self.mcp = FastMCP("UniFi Local Controller MCP Server")
        self.client: Optional[UnifiControllerClient] = None
        self.unifi_service: Optional[UnifiService] = None

    # ------------------------------------------------------------------
    # Destructive ops gate (3-path)
    # ------------------------------------------------------------------

    def _check_destructive(self, params: UnifiParams) -> Optional[ToolResult]:
        """Return a ToolResult gate response if the action is destructive and
        not yet confirmed, or None if execution should proceed."""
        if params.action not in DESTRUCTIVE_ACTIONS:
            return None

        # Path 1: env bypass (CI / automation)
        if os.getenv(
            "UNIFI_MCP_ALLOW_DESTRUCTIVE", os.getenv("ALLOW_DESTRUCTIVE", "false")
        ) == "true":
            return None

        # Path 2: ALLOW_YOLO skips elicitation
        if os.getenv("UNIFI_MCP_ALLOW_YOLO", os.getenv("ALLOW_YOLO", "false")) == "true":
            return None

        # Path 3: explicit confirmation param
        if params.confirm:
            return None

        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"'{params.action.value}' is a destructive operation. "
                        "Pass confirm=true to proceed, or set "
                        "UNIFI_MCP_ALLOW_DESTRUCTIVE=true / "
                        "UNIFI_MCP_ALLOW_YOLO=true in the environment to bypass."
                    ),
                }
            ],
            structured_content={
                "error": "confirmation_required",
                "action": params.action.value,
            },
        )

    # ------------------------------------------------------------------
    # Bearer auth helper
    # ------------------------------------------------------------------

    def _make_bearer_middleware(self):
        """Return a Starlette middleware that validates Authorization: Bearer."""
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse

        expected_token = self._bearer_token

        class BearerAuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                # Skip auth for /health
                if request.url.path == "/health":
                    return await call_next(request)

                if expected_token is None:
                    # NO_AUTH mode — pass through
                    return await call_next(request)

                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        {"error": "Missing or invalid Authorization header"},
                        status_code=401,
                    )
                token = auth_header[len("Bearer ") :]
                if not compare_digest(token, expected_token):
                    return JSONResponse(
                        {"error": "Invalid bearer token"},
                        status_code=403,
                    )
                return await call_next(request)

        return BearerAuthMiddleware

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Initialize the UniFi client and register tools/resources."""
        logger.info("Initializing UniFi MCP Server...")

        self.client = UnifiControllerClient(self.unifi_config)
        try:
            await self.client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to UniFi controller: {e}")
            raise

        self.unifi_service = UnifiService(self.client)

        logger.info("Registering MCP tools...")
        self._register_unified_tool()
        self._register_help_tool()

        logger.info("Registering MCP resources...")
        register_device_resources(self.mcp, self.client)
        register_client_resources(self.mcp, self.client)
        register_network_resources(self.mcp, self.client)
        register_monitoring_resources(self.mcp, self.client)
        register_overview_resources(self.mcp, self.client)
        register_site_resources(self.mcp, self.client)

        logger.info("UniFi MCP Server initialization complete")

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_unified_tool(self) -> None:
        """Register the unified `unifi` tool that handles all actions."""

        @self.mcp.tool()
        async def unifi(
            action: Annotated[
                str,
                Field(
                    description="The action to perform. See UnifiAction enum for all available actions."
                ),
            ],
            site_name: Annotated[
                str,
                Field(
                    default="default",
                    description="UniFi site name (not used by get_sites, get_controller_status, get_user_info)",
                ),
            ] = "default",
            mac: Annotated[
                Optional[str],
                Field(
                    default=None,
                    description="Device or client MAC address (any format, required for device/client operations)",
                ),
            ] = None,
            limit: Annotated[
                Optional[int],
                Field(
                    default=None,
                    description="Maximum number of results to return (default varies by action)",
                ),
            ] = None,
            connected_only: Annotated[
                Optional[bool],
                Field(
                    default=None,
                    description="Only return currently connected clients (get_clients only, default: True)",
                ),
            ] = None,
            active_only: Annotated[
                Optional[bool],
                Field(
                    default=None,
                    description="Only return active/unarchived items (get_alarms only, default: True)",
                ),
            ] = None,
            by_filter: Annotated[
                Optional[str],
                Field(
                    default=None,
                    description="Filter type for DPI stats: 'by_app' or 'by_cat' (get_dpi_stats only, default: 'by_app')",
                ),
            ] = None,
            name: Annotated[
                Optional[str],
                Field(
                    default=None,
                    description="New name for client (set_client_name only)",
                ),
            ] = None,
            note: Annotated[
                Optional[str],
                Field(
                    default=None, description="Note for client (set_client_note only)"
                ),
            ] = None,
            minutes: Annotated[
                Optional[int],
                Field(
                    default=None,
                    description="Duration of guest access in minutes (authorize_guest only, default: 480 = 8 hours)",
                ),
            ] = None,
            up_bandwidth: Annotated[
                Optional[int],
                Field(
                    default=None,
                    description="Upload bandwidth limit in Kbps (authorize_guest only)",
                ),
            ] = None,
            down_bandwidth: Annotated[
                Optional[int],
                Field(
                    default=None,
                    description="Download bandwidth limit in Kbps (authorize_guest only)",
                ),
            ] = None,
            quota: Annotated[
                Optional[int],
                Field(
                    default=None, description="Data quota in MB (authorize_guest only)"
                ),
            ] = None,
            confirm: Annotated[
                Optional[bool],
                Field(
                    default=None,
                    description="Set to true to confirm destructive operations (restart_device, block_client, forget_client, reconnect_client)",
                ),
            ] = None,
        ) -> ToolResult:
            """Unified UniFi tool providing access to all device, client, network, and monitoring operations.

            This consolidated tool replaces 31 individual tools with a single action-based interface.
            All previous functionality is preserved while providing better type safety and efficiency.

            Available Actions:
            - Device Management: get_devices, get_device_by_mac, restart_device, locate_device
            - Client Management: get_clients, reconnect_client, block_client, unblock_client, forget_client, set_client_name, set_client_note
            - Network Configuration: get_sites, get_wlan_configs, get_network_configs, get_port_configs, get_port_forwarding_rules, get_firewall_rules, get_firewall_groups, get_static_routes
            - Monitoring & Statistics: get_controller_status, get_events, get_alarms, get_dpi_stats, get_rogue_aps, start_spectrum_scan, get_spectrum_scan_state, authorize_guest, get_speedtest_results, get_ips_events
            - Authentication: get_user_info

            Destructive actions (restart_device, block_client, forget_client, reconnect_client)
            require confirm=true unless UNIFI_MCP_ALLOW_DESTRUCTIVE=true
            or UNIFI_MCP_ALLOW_YOLO=true is set.
            """
            try:
                try:
                    unifi_action = UnifiAction(action)
                except ValueError:
                    available_actions = [a.value for a in UnifiAction]
                    return ToolResult(
                        content=[
                            {
                                "type": "text",
                                "text": f"Invalid action '{action}'. Available actions: {', '.join(available_actions)}",
                            }
                        ],
                        structured_content={
                            "error": f"Invalid action: {action}",
                            "available_actions": available_actions,
                        },
                    )

                params = UnifiParams(
                    action=unifi_action,
                    site_name=site_name,
                    mac=mac,
                    limit=limit,
                    connected_only=connected_only,
                    active_only=active_only,
                    by_filter=by_filter,
                    name=name,
                    note=note,
                    minutes=minutes,
                    up_bandwidth=up_bandwidth,
                    down_bandwidth=down_bandwidth,
                    quota=quota,
                    confirm=confirm,
                )

                # Destructive ops gate
                gate = self._check_destructive(params)
                if gate is not None:
                    return gate

                if not self.unifi_service:
                    return ToolResult(
                        content=[
                            {"type": "text", "text": "Error: Service not initialized"}
                        ],
                        structured_content={"error": "Service not initialized"},
                    )

                result = await self.unifi_service.execute_action(params)

                # Apply response size cap
                if result.content:
                    capped = []
                    for item in result.content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            capped.append(
                                {
                                    "type": "text",
                                    "text": _truncate_response(item["text"]),
                                }
                            )
                        elif hasattr(item, "text"):
                            capped.append(
                                TextContent(
                                    type="text",
                                    text=_truncate_response(str(item.text)),
                                )
                            )
                        else:
                            capped.append(item)
                    result = ToolResult(
                        content=capped, structured_content=result.structured_content
                    )

                return result

            except Exception as e:
                logger.error(f"Error in unified UniFi tool: {e}")
                return ToolResult(
                    content=[{"type": "text", "text": f"Error: {str(e)}"}],
                    structured_content={"error": str(e)},
                )

        logger.info("Unified UniFi tool registered successfully")

    def _register_help_tool(self) -> None:
        """Register the `unifi_help` tool that returns markdown help."""

        @self.mcp.tool()
        async def unifi_help() -> ToolResult:
            """Return markdown help for all available UniFi MCP actions."""
            help_text = """# UniFi MCP — Tool Reference

## Tool: `unifi`

Single action-based tool for all UniFi operations.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string (required) | Action to perform (see below) |
| `site_name` | string | UniFi site name (default: "default") |
| `mac` | string | Device/client MAC address |
| `limit` | int | Max results to return |
| `connected_only` | bool | get_clients: connected clients only (default: true) |
| `active_only` | bool | get_alarms: active alarms only (default: true) |
| `by_filter` | string | get_dpi_stats: "by_app" or "by_cat" (default: "by_app") |
| `name` | string | set_client_name: new name |
| `note` | string | set_client_note: note text |
| `minutes` | int | authorize_guest: duration in minutes (default: 480) |
| `up_bandwidth` | int | authorize_guest: upload limit in Kbps |
| `down_bandwidth` | int | authorize_guest: download limit in Kbps |
| `quota` | int | authorize_guest: data quota in MB |
| `confirm` | bool | Confirm destructive operations |

### Available Actions

#### Device Management
| Action | MAC Required | Description |
|--------|-------------|-------------|
| `get_devices` | No | List all devices on a site |
| `get_device_by_mac` | Yes | Get device details by MAC |
| `restart_device` | Yes | **Destructive** — Restart a device |
| `locate_device` | Yes | Activate locate LED on a device |

#### Client Management
| Action | MAC Required | Description |
|--------|-------------|-------------|
| `get_clients` | No | List clients (connected_only default: true) |
| `reconnect_client` | Yes | **Destructive** — Force client reconnection |
| `block_client` | Yes | **Destructive** — Block a client |
| `unblock_client` | Yes | Unblock a client |
| `forget_client` | Yes | **Destructive** — Forget/remove a client |
| `set_client_name` | Yes | Set alias name for a client |
| `set_client_note` | Yes | Set note for a client |

#### Network Configuration
| Action | Description |
|--------|-------------|
| `get_sites` | List all sites |
| `get_wlan_configs` | List WLAN configurations |
| `get_network_configs` | List network configurations |
| `get_port_configs` | List port configurations |
| `get_port_forwarding_rules` | List port forwarding rules |
| `get_firewall_rules` | List firewall rules |
| `get_firewall_groups` | List firewall groups |
| `get_static_routes` | List static routes |

#### Monitoring & Statistics
| Action | Description |
|--------|-------------|
| `get_controller_status` | Get controller status |
| `get_events` | Get recent events (limit default: 100) |
| `get_alarms` | Get alarms (active_only default: true) |
| `get_dpi_stats` | Get DPI statistics |
| `get_rogue_aps` | Get rogue access points |
| `start_spectrum_scan` | Start spectrum scan on a device |
| `get_spectrum_scan_state` | Get spectrum scan state |
| `authorize_guest` | Authorize guest access |
| `get_speedtest_results` | Get speedtest history |
| `get_ips_events` | Get IPS/IDS events |

#### Authentication
| Action | Description |
|--------|-------------|
| `get_user_info` | Get authenticated user info |

### Destructive Operations

Actions marked **Destructive** require one of:
1. `confirm=true` parameter
2. `UNIFI_MCP_ALLOW_DESTRUCTIVE=true` environment variable
3. `UNIFI_MCP_ALLOW_YOLO=true` environment variable

## Tool: `unifi_help`

Returns this help text.
"""
            return ToolResult(
                content=[{"type": "text", "text": help_text}],
                structured_content={"help": help_text},
            )

        logger.info("unifi_help tool registered successfully")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def cleanup(self) -> None:
        """Cleanup server resources."""
        logger.info("Cleaning up UniFi MCP Server...")
        if self.client:
            await self.client.disconnect()
        logger.info("UniFi MCP Server cleanup complete")

    def get_app(self):
        """Get the FastMCP HTTP application instance with middleware attached."""
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        base_app = self.mcp.http_app()

        # Add /health endpoint by wrapping in a Starlette app
        async def health(_request):
            return JSONResponse(
                {
                    "status": "ok",
                    "service": "unifi-mcp",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Mount /health on the base_app if it supports middleware/routing,
        # otherwise wrap with a thin Starlette router.
        from starlette.middleware import Middleware
        from starlette.routing import Mount

        middleware = [Middleware(self._make_bearer_middleware())]

        app = Starlette(
            routes=[
                Route("/health", health),
                Mount("/", app=base_app),
            ],
            middleware=middleware,
        )
        return app

    async def run(self) -> None:
        """Run the server (for standalone execution)."""
        import uvicorn

        await self.initialize()

        transport = self.server_config.transport

        try:
            if transport == "stdio":
                logger.info("Starting UniFi MCP Server in stdio transport mode")
                await self.mcp.run_async(transport="stdio")
            else:
                app = self.get_app()
                config = uvicorn.Config(
                    app,
                    host=self.server_config.host,
                    port=self.server_config.port,
                    log_level=self.server_config.log_level.lower(),
                )
                server = uvicorn.Server(config)
                logger.info(
                    f"Starting UniFi MCP Server (HTTP) on "
                    f"{self.server_config.host}:{self.server_config.port}"
                )
                await server.serve()

        finally:
            await self.cleanup()
