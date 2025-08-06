"""
Monitoring and statistics tools for UniFi MCP Server.

Provides tools for accessing controller status, events, alarms,
statistics, and security monitoring data.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_timestamp, format_data_values

logger = logging.getLogger(__name__)


def register_monitoring_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all monitoring and statistics tools."""
    
    @mcp.tool()
    async def get_controller_status() -> Dict[str, Any]:
        """
        Get controller system information and status.
        
        Returns:
            Controller status with system information
        """
        try:
            # Get basic controller status
            result = await client._make_request("GET", "/status", site_name="")
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {
                "status": "online",
                "server_version": result.get("server_version", "Unknown"),
                "up": result.get("up", False),
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error getting controller status: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_events(limit: int = 100, site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get recent controller events.
        
        Args:
            limit: Maximum number of events to return (default: 100)
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of recent events with formatted timestamps
        """
        try:
            events = await client.get_events(site_name, limit)
            
            if isinstance(events, dict) and "error" in events:
                return [events]
            
            if not isinstance(events, list):
                return [{"error": "Unexpected response format"}]
            
            # Format events for clean output
            formatted_events = []
            for event in events[-limit:]:  # Get most recent events
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
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_alarms(active_only: bool = True, site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get controller alarms.
        
        Args:
            active_only: Only return active/unarchived alarms (default: True)
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of alarms with formatted information
        """
        try:
            alarms = await client.get_alarms(site_name)
            
            if isinstance(alarms, dict) and "error" in alarms:
                return [alarms]
            
            if not isinstance(alarms, list):
                return [{"error": "Unexpected response format"}]
            
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
            
            return formatted_alarms
            
        except Exception as e:
            logger.error(f"Error getting alarms: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_dpi_stats(by_filter: str = "by_app", site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get Deep Packet Inspection (DPI) statistics.
        
        Args:
            by_filter: Filter type - 'by_app' or 'by_cat' (default: 'by_app')
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of DPI statistics with formatted data usage
        """
        try:
            dpi_stats = await client.get_dpi_stats(site_name)
            
            if isinstance(dpi_stats, dict) and "error" in dpi_stats:
                return [dpi_stats]
            
            if not isinstance(dpi_stats, list):
                return [{"error": "Unexpected response format"}]
            
            # Format DPI stats with data formatting
            formatted_stats = []
            for stat in dpi_stats:
                formatted_stat = format_data_values(stat)
                
                # Add human-readable summary
                formatted_stat["summary"] = {
                    "application": stat.get("app", stat.get("cat", "Unknown")),
                    "total_bytes": formatted_stat.get("tx_bytes", "0 B") + " / " + formatted_stat.get("rx_bytes", "0 B"),
                    "last_seen": format_timestamp(stat.get("time", 0))
                }
                
                formatted_stats.append(formatted_stat)
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Error getting DPI stats: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_rogue_aps(site_name: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get detected rogue access points (filtered to prevent large responses).
        
        Args:
            site_name: UniFi site name (default: "default")
            limit: Maximum number of rogue APs to return (default: 20, max: 50)
            
        Returns:
            List of rogue access points with signal information
        """
        try:
            # Limit the maximum to prevent overwhelming responses
            limit = min(limit, 50)
            
            rogue_aps = await client.get_rogue_aps(site_name)
            
            if isinstance(rogue_aps, dict) and "error" in rogue_aps:
                return [rogue_aps]
            
            if not isinstance(rogue_aps, list):
                return [{"error": "Unexpected response format"}]
            
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
            
            return formatted_rogues
            
        except Exception as e:
            logger.error(f"Error getting rogue APs: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def start_spectrum_scan(mac: str, site_name: str = "default") -> Dict[str, Any]:
        """
        Start RF spectrum scan on access point.
        
        Args:
            mac: Access point MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of the spectrum scan start command
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            data = {
                "cmd": "spectrum-scan",
                "mac": normalized_mac
            }
            
            result = await client._make_request("POST", "/cmd/devmgr", site_name=site_name, data=data)
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {
                "success": True,
                "message": f"Spectrum scan started on AP {mac}",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error starting spectrum scan on {mac}: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_spectrum_scan_state(mac: str, site_name: str = "default") -> Dict[str, Any]:
        """
        Get RF spectrum scan state and results.
        
        Args:
            mac: Access point MAC address (any format)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Spectrum scan state and results
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
            result = await client._make_request("GET", f"/stat/spectrum-scan/{normalized_mac}", site_name=site_name)
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {
                "mac": mac,
                "scan_data": result
            }
            
        except Exception as e:
            logger.error(f"Error getting spectrum scan state for {mac}: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def authorize_guest(
        mac: str,
        minutes: int = 480,
        up_bandwidth: int = None,
        down_bandwidth: int = None,
        quota: int = None,
        site_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Authorize guest client for network access.
        
        Args:
            mac: Client MAC address (any format)
            minutes: Duration of access in minutes (default: 480 = 8 hours)
            up_bandwidth: Upload bandwidth limit in Kbps (optional)
            down_bandwidth: Download bandwidth limit in Kbps (optional)
            quota: Data quota in MB (optional)
            site_name: UniFi site name (default: "default")
            
        Returns:
            Result of guest authorization
        """
        try:
            # Normalize MAC address
            normalized_mac = mac.lower().replace("-", ":").replace(".", ":")
            
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
            
            result = await client._make_request("POST", "/cmd/stamgr", site_name=site_name, data=data)
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {
                "success": True,
                "message": f"Guest {mac} authorized for {minutes} minutes",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Error authorizing guest {mac}: {e}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_speedtest_results(site_name: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get historical internet speed test results.
        
        Args:
            site_name: UniFi site name (default: "default")
            limit: Maximum number of results to return (default: 20)
            
        Returns:
            List of speed test results with formatted information
        """
        try:
            # Use the archive speedtest endpoint with time range
            import time
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            start_time = end_time - (30 * 24 * 60 * 60 * 1000)  # 30 days ago
            
            data = {
                "start": start_time,
                "end": end_time,
                "attrs": ["time", "xput_download", "xput_upload", "latency", "ping", "jitter"]
            }
            
            results = await client._make_request("POST", "/stat/report/archive.speedtest", 
                                               site_name=site_name, data=data)
            
            if isinstance(results, dict) and "error" in results:
                return [results]
            
            if not isinstance(results, list):
                return [{"error": "Unexpected response format"}]
            
            # Format speed test results for clean output
            formatted_results = []
            for result in results[-limit:]:  # Get the most recent results
                formatted_result = {
                    "timestamp": format_timestamp(result.get("time", 0)),
                    "download_mbps": round(result.get("xput_download", 0) / 1000000, 2),
                    "upload_mbps": round(result.get("xput_upload", 0) / 1000000, 2),
                    "latency_ms": result.get("latency", 0),
                    "ping_ms": result.get("ping", 0),
                    "jitter_ms": result.get("jitter", 0),
                    "server": result.get("server", "Unknown")
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting speed test results: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_ips_events(site_name: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get IPS/IDS threat detection events for security monitoring.
        
        Args:
            site_name: UniFi site name (default: "default")
            limit: Maximum number of events to return (default: 50)
            
        Returns:
            List of IPS events with formatted threat information
        """
        try:
            # Use the IPS events endpoint with time range
            import time
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago
            
            data = {
                "start": start_time,
                "end": end_time,
                "attrs": ["time", "src_ip", "dst_ip", "proto", "app_proto", "signature", 
                         "category", "action", "severity", "msg"]
            }
            
            events = await client._make_request("POST", "/stat/ips/event", 
                                              site_name=site_name, data=data)
            
            if isinstance(events, dict) and "error" in events:
                return [events]
            
            if not isinstance(events, list):
                return [{"error": "Unexpected response format"}]
            
            # Format IPS events for clean output
            formatted_events = []
            for event in events[-limit:]:  # Get the most recent events
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
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error getting IPS events: {e}")
            return [{"error": str(e)}]