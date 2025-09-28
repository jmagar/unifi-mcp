"""
Monitoring service for UniFi MCP Server.

Handles all monitoring and statistics operations including controller status,
events, alarms, security monitoring, and performance metrics.
"""

import logging
import time
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .base import BaseService
from ..models.enums import UnifiAction
from ..models.params import UnifiParams
from ..formatters import (
    format_timestamp,
    format_data_values,
    format_events_list,
    format_alarms_list,
    format_dpi_stats_list,
    format_rogue_aps_list,
    format_speedtests_list,
    format_ips_events_list,
)

logger = logging.getLogger(__name__)


class MonitoringService(BaseService):
    """Service for monitoring and statistics operations.

    Provides consolidated access to controller status, events, alarms,
    statistics, and security monitoring data.
    """

    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute monitoring-related actions.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with action response
        """
        action_map = {
            UnifiAction.GET_CONTROLLER_STATUS: self._get_controller_status,
            UnifiAction.GET_EVENTS: self._get_events,
            UnifiAction.GET_ALARMS: self._get_alarms,
            UnifiAction.GET_DPI_STATS: self._get_dpi_stats,
            UnifiAction.GET_ROGUE_APS: self._get_rogue_aps,
            UnifiAction.START_SPECTRUM_SCAN: self._start_spectrum_scan,
            UnifiAction.GET_SPECTRUM_SCAN_STATE: self._get_spectrum_scan_state,
            UnifiAction.AUTHORIZE_GUEST: self._authorize_guest,
            UnifiAction.GET_SPEEDTEST_RESULTS: self._get_speedtest_results,
            UnifiAction.GET_IPS_EVENTS: self._get_ips_events,
        }

        handler = action_map.get(params.action)
        if not handler:
            return self.create_error_result(
                f"Monitoring action {params.action} not supported"
            )

        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"Error executing monitoring action {params.action}: {e}")
            return self.create_error_result(str(e))

    async def _get_controller_status(self, params: UnifiParams) -> ToolResult:
        """Get controller system information and status."""
        try:
            # Get basic controller status
            result = await self.client._make_request("GET", "/status", site_name="")

            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content={"error": result.get('error','unknown error'), "raw": result}
                )

            resp = {
                "status": "online",
                "server_version": result.get("server_version", "Unknown"),
                "up": result.get("up", False),
                "details": result
            }
            up_icon = "✓" if resp.get("up") else "✗"
            text = f"Controller Status\n  Version: {resp['server_version']} | Up: {up_icon}"
            return ToolResult(
                content=[TextContent(type="text", text=text)],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error getting controller status: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _get_events(self, params: UnifiParams) -> ToolResult:
        """Get recent controller events."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            limit = params.limit or defaults.get('limit', 100)

            events = await self.client.get_events(site_name, limit)

            if isinstance(events, dict) and "error" in events:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {events.get('error','unknown error')}")],
                    structured_content={"error": events.get('error','unknown error'), "raw": events}
                )

            if not isinstance(events, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format", "raw": events}
                )

            # Format events for clean output
            formatted_events = []
            events_sorted = sorted(
                events, key=lambda e: e.get("time", e.get("timestamp", 0)), reverse=True
            )[:limit]
            for event in events_sorted:
                formatted_event = {
                    "timestamp": format_timestamp(event.get("time", 0)),
                    "type": event.get("key", "Unknown"),
                    "message": event.get("msg", "No message"),
                    "device": event.get("ap", event.get("gw", event.get("sw", "Unknown"))),
                    "user": event.get("user", "System"),
                    "subsystem": event.get("subsystem", "Unknown"),
                    "details": {
                        k: v for k, v in event.items()
                        if k not in ["time", "key", "msg", "ap", "gw", "sw", "user", "subsystem"]
                    }
                }
                formatted_events.append(formatted_event)

            summary_text = format_events_list(formatted_events)
            return self.create_success_result(
                text=summary_text,
                data=formatted_events,
                success_message=f"Retrieved {len(formatted_events)} events"
            )

        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )

    async def _get_alarms(self, params: UnifiParams) -> ToolResult:
        """Get controller alarms."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            active_only = params.active_only if params.active_only is not None else defaults.get('active_only', True)

            alarms = await self.client.get_alarms(site_name)

            if isinstance(alarms, dict) and "error" in alarms:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {alarms.get('error','unknown error')}")],
                    structured_content={"error": alarms.get('error','unknown error'), "raw": alarms}
                )

            if not isinstance(alarms, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format", "raw": alarms}
                )

            # Filter and format alarms
            formatted_alarms = []
            for alarm in alarms:
                # Skip archived alarms if active_only is True
                if active_only and alarm.get("archived", False):
                    continue

                formatted_alarm = {
                    "timestamp": format_timestamp(alarm.get("time", 0)),
                    "type": alarm.get("key", "Unknown"),
                    "message": alarm.get("msg", "No message"),
                    "severity": alarm.get("catname", "Unknown"),
                    "device": alarm.get("ap", alarm.get("gw", alarm.get("sw", "Unknown"))),
                    "archived": alarm.get("archived", False),
                    "handled": alarm.get("handled", False),
                    "site_id": alarm.get("site_id", "Unknown")
                }
                formatted_alarms.append(formatted_alarm)

            summary_text = format_alarms_list(formatted_alarms)
            return self.create_success_result(
                text=summary_text,
                data=formatted_alarms,
                success_message=f"Retrieved {len(formatted_alarms)} alarms"
            )

        except Exception as e:
            logger.error(f"Error getting alarms: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )

    async def _get_dpi_stats(self, params: UnifiParams) -> ToolResult:
        """Get Deep Packet Inspection (DPI) statistics."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            by_filter = params.by_filter or defaults.get('by_filter', 'by_app')

            dpi_stats = await self.client.get_dpi_stats(site_name)

            if isinstance(dpi_stats, dict) and "error" in dpi_stats:
                return self.create_error_result(dpi_stats.get('error','unknown error'), dpi_stats)

            if not isinstance(dpi_stats, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format", "raw": dpi_stats}
                )

            # Format DPI stats with data formatting
            formatted_stats = []
            for stat in dpi_stats:
                formatted_stat = format_data_values(stat)

                # Add human-readable summary
                tx_raw = formatted_stat.get("tx_bytes_raw", 0) or 0
                rx_raw = formatted_stat.get("rx_bytes_raw", 0) or 0
                formatted_stat["summary"] = {
                    "application": stat.get("app", stat.get("cat", "Unknown")),
                    "tx": formatted_stat.get("tx_bytes", "0 B"),
                    "rx": formatted_stat.get("rx_bytes", "0 B"),
                    "total_bytes_raw": tx_raw + rx_raw,
                    "last_seen": format_timestamp(stat.get("time", 0))
                }

                formatted_stats.append(formatted_stat)

            summary_text = format_dpi_stats_list(formatted_stats)
            return self.create_success_result(
                text=summary_text,
                data=formatted_stats,
                success_message=f"Retrieved {len(formatted_stats)} DPI statistics"
            )

        except Exception as e:
            logger.error(f"Error getting DPI stats: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )

    async def _get_rogue_aps(self, params: UnifiParams) -> ToolResult:
        """Get detected rogue access points (filtered to prevent large responses)."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            limit = params.limit or defaults.get('limit', 20)

            # Limit the maximum to prevent overwhelming responses
            limit = min(limit, 50)

            rogue_aps = await self.client.get_rogue_aps(site_name)

            if isinstance(rogue_aps, dict) and "error" in rogue_aps:
                return self.create_error_result(rogue_aps.get('error','unknown error'), rogue_aps)

            if not isinstance(rogue_aps, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format", "raw": rogue_aps}
                )

            # Sort by signal strength (strongest first) and limit results
            filtered_rogues = sorted(rogue_aps,
                                   key=lambda x: x.get("rssi", -100),
                                   reverse=True)[:limit]

            # Format rogue APs for clean output
            formatted_rogues = []

            # Add summary if results were limited
            if len(rogue_aps) > limit:
                formatted_rogues.append({
                    "summary": f"Showing top {limit} of {len(rogue_aps)} detected rogue APs (sorted by signal strength)"
                })

            for rogue in filtered_rogues:
                rssi = rogue.get("rssi", "Unknown")
                signal_str = f"{rssi} dBm" if isinstance(rssi, (int, float)) else str(rssi)

                # Determine threat level based on signal strength
                if isinstance(rssi, (int, float)):
                    if rssi > -60:
                        threat_level = "High"
                    elif rssi > -80:
                        threat_level = "Medium"
                    else:
                        threat_level = "Low"
                else:
                    threat_level = "Unknown"

                formatted_rogue = {
                    "ssid": rogue.get("essid", "Hidden"),
                    "bssid": rogue.get("bssid", "Unknown"),
                    "channel": rogue.get("channel", "Unknown"),
                    "frequency": rogue.get("freq", "Unknown"),
                    "signal_strength": signal_str,
                    "security": rogue.get("security", "Unknown"),
                    "threat_level": threat_level,
                    "first_seen": format_timestamp(rogue.get("first_seen", 0)),
                    "last_seen": format_timestamp(rogue.get("last_seen", 0)),
                    "detected_by": rogue.get("ap_mac", "Unknown")
                }
                formatted_rogues.append(formatted_rogue)

            # Build compact text; include summary if present at index 0
            text_items = [item for item in formatted_rogues if isinstance(item, dict) and item.get('ssid')]
            header = next((item.get('summary') for item in formatted_rogues if isinstance(item, dict) and 'summary' in item), None)
            summary_text = format_rogue_aps_list(text_items)
            if header:
                summary_text = header + "\n" + summary_text
            return self.create_success_result(
                text=summary_text,
                data=formatted_rogues,
                success_message=f"Retrieved {len(text_items)} rogue access points"
            )

        except Exception as e:
            logger.error(f"Error getting rogue APs: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )

    async def _start_spectrum_scan(self, params: UnifiParams) -> ToolResult:
        """Start RF spectrum scan on access point."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            data = {
                "cmd": "spectrum-scan",
                "mac": normalized_mac
            }

            result = await self.client._make_request("POST", "/cmd/devmgr", site_name=site_name, data=data)

            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Spectrum scan started on AP {params.mac}",
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Spectrum scan started: {params.mac}")],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error starting spectrum scan on {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _get_spectrum_scan_state(self, params: UnifiParams) -> ToolResult:
        """Get RF spectrum scan state and results."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            result = await self.client._make_request("GET", f"/stat/spectrum-scan/{normalized_mac}", site_name=site_name)

            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {"mac": params.mac, "scan_data": result}
            text = f"Spectrum Scan State\n  MAC: {params.mac} | Data: {'✓' if bool(result) else '✗'}"
            return ToolResult(
                content=[TextContent(type="text", text=text)],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error getting spectrum scan state for {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _authorize_guest(self, params: UnifiParams) -> ToolResult:
        """Authorize guest client for network access."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            # Normalize MAC address
            normalized_mac = self.normalize_mac(params.mac)

            minutes = params.minutes or defaults.get('minutes', 480)
            up_bandwidth = params.up_bandwidth
            down_bandwidth = params.down_bandwidth
            quota = params.quota

            if minutes <= 0:
                return self.create_error_result("minutes must be > 0", {"error": "invalid_minutes"})
            for k, v in (("up", up_bandwidth), ("down", down_bandwidth), ("bytes_mb", quota)):
                if v is not None and v < 0:
                    return self.create_error_result(f"{k} must be non-negative", {"error": f"invalid_{k}"})

            data = {
                "cmd": "authorize-guest",
                "mac": normalized_mac,
                "minutes": minutes
            }

            if up_bandwidth is not None:
                data["up"] = up_bandwidth
            if down_bandwidth is not None:
                data["down"] = down_bandwidth
            if quota is not None:
                data["bytes"] = quota * 1024 * 1024  # Convert MB to bytes

            result = await self.client._make_request("POST", "/cmd/stamgr", site_name=site_name, data=data)

            if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=result
                )

            resp = {
                "success": True,
                "message": f"Guest {params.mac} authorized for {minutes} minutes",
                "details": result
            }
            text = f"Guest authorized: {params.mac} | {minutes} min"
            return ToolResult(
                content=[TextContent(type="text", text=text)],
                structured_content=resp
            )

        except Exception as e:
            logger.error(f"Error authorizing guest {params.mac}: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e)}
            )

    async def _get_speedtest_results(self, params: UnifiParams) -> ToolResult:
        """Get historical internet speed test results."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            limit = params.limit or defaults.get('limit', 20)

            # Use the archive speedtest endpoint with time range
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            start_time = end_time - (30 * 24 * 60 * 60 * 1000)  # 30 days ago

            data = {
                "start": start_time,
                "end": end_time,
                "attrs": ["time", "xput_download", "xput_upload", "latency", "ping", "jitter"]
            }

            results = await self.client._make_request("POST", "/stat/report/archive.speedtest",
                                                   site_name=site_name, data=data)

            if isinstance(results, dict) and "error" in results:
                return self.create_error_result(results.get('error','unknown error'), results)

            if not isinstance(results, list):
                return self.create_error_result(f"Unexpected response format: {type(results).__name__}", {"error": f"Unexpected response format: {type(results).__name__}", "data": results})

            # Format speed test results for clean output
            formatted_results = []
            for result in results[-limit:]:  # Get the most recent results
                # Try different possible field names for speed values
                download_speed = (result.get("xput_download", 0) or
                                result.get("download", 0) or
                                result.get("download_speed", 0) or
                                result.get("down", 0))
                upload_speed = (result.get("xput_upload", 0) or
                              result.get("upload", 0) or
                              result.get("upload_speed", 0) or
                              result.get("up", 0))

                formatted_result = {
                    "timestamp": format_timestamp(result.get("time", 0)),
                    "download_mbps": round(download_speed, 2) if download_speed else 0.0,
                    "upload_mbps": round(upload_speed, 2) if upload_speed else 0.0,
                    "latency_ms": result.get("latency", result.get("rtt", 0)),
                    "ping_ms": result.get("ping", 0),
                    "jitter_ms": result.get("jitter", 0),
                    "server": result.get("server", result.get("test_server", "Unknown"))
                }
                formatted_results.append(formatted_result)

            summary_text = format_speedtests_list(formatted_results)
            return self.create_success_result(
                text=summary_text,
                data=formatted_results,
                success_message=f"Retrieved {len(formatted_results)} speed test results"
            )

        except Exception as e:
            logger.error(f"Error getting speed test results: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )

    async def _get_ips_events(self, params: UnifiParams) -> ToolResult:
        """Get IPS/IDS threat detection events for security monitoring."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')
            limit = params.limit or defaults.get('limit', 50)

            # Use the IPS events endpoint with time range
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago

            data = {
                "start": start_time,
                "end": end_time,
                "attrs": ["time", "src_ip", "dst_ip", "proto", "app_proto", "signature",
                         "category", "action", "severity", "msg"]
            }

            events = await self.client._make_request("POST", "/stat/ips/event",
                                                  site_name=site_name, data=data)

            if isinstance(events, dict) and "error" in events:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {events.get('error','unknown error')}")],
                    structured_content={"error": events.get('error','unknown error'), "raw": events}
                )

            if not isinstance(events, list):
                return ToolResult(
                    content=[TextContent(type="text", text="Error: Unexpected response format")],
                    structured_content={"error": "Unexpected response format", "raw": events}
                )

            # Format IPS events for clean output
            formatted_events = []
            events_sorted = sorted(
                events, key=lambda e: e.get("time", e.get("timestamp", 0)), reverse=True
            )[:limit]
            for event in events_sorted:
                formatted_event = {
                    "timestamp": format_timestamp(event.get("time", 0)),
                    "source_ip": event.get("src_ip", "Unknown"),
                    "destination_ip": event.get("dst_ip", "Unknown"),
                    "protocol": event.get("proto", "Unknown"),
                    "app_protocol": event.get("app_proto", "Unknown"),
                    "signature": event.get("signature", "Unknown"),
                    "category": event.get("category", "Unknown"),
                    "action": event.get("action", "Unknown"),
                    "severity": event.get("severity", "Unknown"),
                    "message": event.get("msg", "No message")
                }
                formatted_events.append(formatted_event)

            summary_text = format_ips_events_list(formatted_events)
            return self.create_success_result(
                text=summary_text,
                data=formatted_events,
                success_message=f"Retrieved {len(formatted_events)} IPS events"
            )

        except Exception as e:
            logger.error(f"Error getting IPS events: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                structured_content={"error": str(e), "raw": None}
            )