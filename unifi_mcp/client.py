"""
UniFi Controller Client for authentication and API communication.

Handles connection to both UDM Pro/UniFi OS and legacy controllers with
automatic session management, authentication, and request handling.
"""

import json
import logging
import base64
from typing import Any, Dict, Optional, Union
import httpx

from .config import UniFiConfig
from .formatters import (
    format_client_summary, format_device_summary, format_site_summary,
    format_bytes
)

logger = logging.getLogger(__name__)


class UnifiControllerClient:
    """Client for UniFi Controller API communication."""
    
    def __init__(self, config: UniFiConfig):
        """Initialize the UniFi controller client."""
        self.config = config
        self.session: Optional[httpx.AsyncClient] = None
        self.csrf_token: Optional[str] = None
        self.is_authenticated = False
        
        # Determine API base path
        self.api_base = "/proxy/network/api" if config.is_udm_pro else "/api"
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Initialize session and authenticate."""
        if not self.session:
            self.session = httpx.AsyncClient(
                verify=self.config.verify_ssl,
                timeout=30.0
            )
        
        await self.authenticate()
        
    async def disconnect(self) -> None:
        """Close session and cleanup."""
        if self.session:
            await self.session.aclose()
            self.session = None
        self.is_authenticated = False
        self.csrf_token = None
        
    async def authenticate(self) -> bool:
        """Authenticate with the UniFi controller."""
        if not self.session:
            raise RuntimeError("Session not initialized. Call connect() first.")
            
        try:
            # Determine login endpoint and payload
            if self.config.is_udm_pro:
                login_url = f"{self.config.controller_url}/api/auth/login"
                login_data = {
                    "username": self.config.username,
                    "password": self.config.password
                }
            else:
                login_url = f"{self.config.controller_url}{self.api_base}/login"
                login_data = {
                    "username": self.config.username,
                    "password": self.config.password,
                    "remember": True
                }
            
            logger.debug(f"Authenticating to {login_url}")
            
            response = await self.session.post(login_url, json=login_data)
            if response.status_code != 200:
                logger.error(f"Authentication failed with status {response.status_code}")
                return False
            
            # Handle UDM Pro authentication
            if self.config.is_udm_pro:
                # Extract CSRF token from JWT
                token_cookie = self.session.cookies.get("TOKEN")
                
                if token_cookie:
                    try:
                        # Decode JWT payload (second part)
                        jwt_parts = token_cookie.split('.')
                        if len(jwt_parts) >= 2:
                            # Add padding if needed
                            payload = jwt_parts[1]
                            payload += '=' * (4 - len(payload) % 4)
                            decoded = base64.urlsafe_b64decode(payload)
                            jwt_data = json.loads(decoded)
                            self.csrf_token = jwt_data.get('csrfToken')
                            logger.debug("Extracted CSRF token from JWT")
                    except Exception as e:
                        logger.warning(f"Failed to extract CSRF token: {e}")
            
            self.is_authenticated = True
            logger.info("Successfully authenticated to UniFi controller")
            return True
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
            
    async def ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication session."""
        if not self.is_authenticated:
            await self.authenticate()
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        site_name: str = "default",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], list]:
        """Make an authenticated request to the UniFi controller."""
        await self.ensure_authenticated()
        
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        # Build URL
        if site_name == "":
            # Special case for /self/sites endpoint
            url = f"{self.config.controller_url}{self.api_base}{endpoint}"
        else:
            # Standard site-specific endpoint
            url = f"{self.config.controller_url}{self.api_base}/s/{site_name}{endpoint}"
        
        # Setup headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add CSRF token for UDM Pro
        if self.config.is_udm_pro and self.csrf_token:
            headers["X-CSRF-Token"] = self.csrf_token
            
        try:
            logger.debug(f"Making {method} request to {url}")
            
            response = await self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            )
            
            if response.status_code == 401:
                logger.warning("Received 401, re-authenticating")
                self.is_authenticated = False
                await self.authenticate()
                
                # Retry the request
                retry_response = await self.session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                if retry_response.status_code != 200:
                    logger.error(f"Request failed with status {retry_response.status_code}")
                    return {"error": f"Request failed with status {retry_response.status_code}"}
                    
                response_data = retry_response.json()
                
            elif response.status_code != 200:
                logger.error(f"Request failed with status {response.status_code}")
                return {"error": f"Request failed with status {response.status_code}"}
            else:
                response_data = response.json()
            
            # Extract data from UniFi response format
            if isinstance(response_data, dict) and "data" in response_data:
                return response_data["data"]
            
            return response_data
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
            
    async def get_sites(self) -> Union[Dict[str, Any], list]:
        """Get all sites from the controller."""
        return await self._make_request("GET", "/self/sites", site_name="")
        
    async def get_devices(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get all devices for a site."""
        return await self._make_request("GET", "/stat/device", site_name=site_name)
        
    async def get_clients(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get all active clients for a site."""
        return await self._make_request("GET", "/stat/sta", site_name=site_name)
        
    async def restart_device(self, mac: str, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Restart a device by MAC address."""
        data = {
            "cmd": "restart",
            "mac": mac.lower().replace("-", ":").replace(".", ":")
        }
        return await self._make_request("POST", "/cmd/devmgr", site_name=site_name, data=data)
        
    async def locate_device(self, mac: str, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Enable locate LED on a device."""
        data = {
            "cmd": "set-locate",
            "mac": mac.lower().replace("-", ":").replace(".", ":")
        }
        return await self._make_request("POST", "/cmd/devmgr", site_name=site_name, data=data)
        
    async def reconnect_client(self, mac: str, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Force reconnect a client."""
        data = {
            "cmd": "kick-sta",
            "mac": mac.lower().replace("-", ":").replace(".", ":")
        }
        return await self._make_request("POST", "/cmd/stamgr", site_name=site_name, data=data)
        
    async def get_events(self, site_name: str = "default", limit: int = 100) -> Union[Dict[str, Any], list]:
        """Get recent events."""
        data = {"_limit": limit}
        return await self._make_request("POST", "/stat/event", site_name=site_name, data=data)
        
    async def get_alarms(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get active alarms."""
        return await self._make_request("GET", "/list/alarm", site_name=site_name)
        
    async def get_site_health(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get site health information."""
        return await self._make_request("GET", "/stat/health", site_name=site_name)
        
    async def get_wlan_configs(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get WLAN configurations."""
        return await self._make_request("GET", "/rest/wlanconf", site_name=site_name)
        
    async def get_network_configs(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get network/VLAN configurations."""
        return await self._make_request("GET", "/rest/networkconf", site_name=site_name)
        
    async def get_port_configs(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get switch port profile configurations."""
        return await self._make_request("GET", "/rest/portconf", site_name=site_name)
        
    async def get_port_forwarding_rules(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get port forwarding rules."""
        return await self._make_request("GET", "/list/portforward", site_name=site_name)
        
    async def get_dpi_stats(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get DPI statistics."""
        return await self._make_request("GET", "/stat/dpi", site_name=site_name)
        
    async def get_dashboard_metrics(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get dashboard metrics."""
        return await self._make_request("GET", "/stat/dashboard", site_name=site_name)
        
    async def get_rogue_aps(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get detected rogue access points."""
        data = {"within": 24}  # Last 24 hours
        return await self._make_request("POST", "/stat/rogueap", site_name=site_name, data=data)
        
    async def get_speedtest_results(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get speed test results."""
        data = {"attrs": ["xput_download", "xput_upload", "latency", "time"]}
        return await self._make_request("POST", "/stat/report/archive.speedtest", site_name=site_name, data=data)
        
    async def get_threat_events(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get IPS threat detection events."""
        data = {"within": 24}  # Last 24 hours
        return await self._make_request("POST", "/stat/ips/event", site_name=site_name, data=data)
    
    # ==================== FORMATTED DATA METHODS ====================
    # These methods return structured, formatted data for tools
    
    async def get_clients_formatted(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get clients with formatted, structured data."""
        clients = await self.get_clients(site_name)
        if isinstance(clients, dict) and "error" in clients:
            return clients
        if not isinstance(clients, list):
            return {"error": "Unexpected response format"}
        
        return [format_client_summary(client) for client in clients]
    
    async def get_devices_formatted(self, site_name: str = "default") -> Union[Dict[str, Any], list]:
        """Get devices with formatted, structured data."""
        devices = await self.get_devices(site_name)
        if isinstance(devices, dict) and "error" in devices:
            return devices
        if not isinstance(devices, list):
            return {"error": "Unexpected response format"}
        
        formatted_devices = []
        for device in devices:
            try:
                formatted_devices.append(format_device_summary(device))
            except Exception as e:
                # Handle formatting errors gracefully
                formatted_devices.append({
                    "name": device.get("name", "Unknown Device"),
                    "mac": device.get("mac", "Unknown"),
                    "error": f"Formatting error: {str(e)}"
                })
        return formatted_devices
    
    async def get_sites_formatted(self) -> Union[Dict[str, Any], list]:
        """Get sites with formatted, structured data."""
        sites = await self.get_sites()
        if isinstance(sites, dict) and "error" in sites:
            return sites
        if not isinstance(sites, list):
            return {"error": "Unexpected response format"}
        
        return [format_site_summary(site) for site in sites]
    
    # ==================== SUMMARY METHODS ====================
    # These methods return concise text summaries for resources
    
    async def get_clients_summary(self, site_name: str = "default") -> str:
        """Get concise clients summary."""
        formatted_clients = await self.get_clients_formatted(site_name)
        if isinstance(formatted_clients, dict) and "error" in formatted_clients:
            return f"Error: {formatted_clients['error']}"
        
        if not formatted_clients:
            return "📱 No clients connected"
        
        wireless = [c for c in formatted_clients if c.get('connection_type') == 'Wireless']
        wired = [c for c in formatted_clients if c.get('connection_type') == 'Wired']
        
        summary = f"📱 {len(formatted_clients)} clients: "
        parts = []
        
        if wireless:
            top_names = [c.get('name', 'Device') for c in wireless[:2]]
            parts.append(f"📶{len(wireless)} wireless ({', '.join(top_names)}{'...' if len(wireless) > 2 else ''})")
        
        if wired:
            top_names = [c.get('name', 'Device') for c in wired[:2]]
            parts.append(f"🔌{len(wired)} wired ({', '.join(top_names)}{'...' if len(wired) > 2 else ''})")
        
        return summary + " | ".join(parts)
    
    async def get_devices_summary(self, site_name: str = "default") -> str:
        """Get concise devices summary."""
        formatted_devices = await self.get_devices_formatted(site_name)
        if isinstance(formatted_devices, dict) and "error" in formatted_devices:
            return f"Error: {formatted_devices['error']}"
        
        if not formatted_devices:
            return "📱 No devices found"
        
        online = len([d for d in formatted_devices if d.get('status') == 'Online'])
        aps = len([d for d in formatted_devices if d.get('type') == 'Access Point'])
        gws = len([d for d in formatted_devices if d.get('type') == 'Gateway'])
        switches = len([d for d in formatted_devices if d.get('type') == 'Switch'])
        
        summary = f"🏭 {len(formatted_devices)} devices ({online} online): "
        parts = []
        if aps > 0:
            parts.append(f"📡{aps}AP")
        if gws > 0:
            parts.append(f"🌐{gws}GW")
        if switches > 0:
            parts.append(f"🔌{switches}SW")
        
        return summary + " ".join(parts)
    
    async def get_events_summary(self, site_name: str = "default", limit: int = 100) -> str:
        """Get concise events summary."""
        events = await self.get_events(site_name, limit)
        if isinstance(events, dict) and "error" in events:
            return f"Error: {events['error']}"
        if not isinstance(events, list):
            return "Error: Unexpected response format"
        
        if not events:
            return "📋 No events"
        
        # Count event types
        connects = len([e for e in events if "connected" in e.get("key", "").lower()])
        disconnects = len([e for e in events if "disconnected" in e.get("key", "").lower()])
        roams = len([e for e in events if "roam" in e.get("key", "").lower()])
        other = len(events) - connects - disconnects - roams
        
        summary = f"📋 {len(events)} events: "
        parts = []
        if connects > 0:
            parts.append(f"🔗{connects}")
        if disconnects > 0:
            parts.append(f"🔌{disconnects}")
        if roams > 0:
            parts.append(f"📶{roams}")
        if other > 0:
            parts.append(f"📋{other}")
        
        return summary + " ".join(parts)
    
    async def get_sites_summary(self) -> str:
        """Get concise sites summary."""
        formatted_sites = await self.get_sites_formatted()
        if isinstance(formatted_sites, dict) and "error" in formatted_sites:
            return f"Error: {formatted_sites['error']}"
        
        if not formatted_sites:
            return "🏢 No sites found"
        
        summary = f"🏢 {len(formatted_sites)} sites: "
        site_names = [s.get('name', 'Site') for s in formatted_sites[:3]]
        summary += ", ".join(site_names)
        if len(formatted_sites) > 3:
            summary += f" +{len(formatted_sites) - 3} more"
        
        return summary
    
    async def get_alarms_summary(self, site_name: str = "default") -> str:
        """Get concise alarms summary."""
        alarms = await self.get_alarms(site_name)
        if isinstance(alarms, dict) and "error" in alarms:
            return f"Error: {alarms['error']}"
        if not isinstance(alarms, list):
            return "Error: Unexpected response format"
        
        active_alarms = [a for a in alarms if not a.get("archived", False)]
        if not active_alarms:
            return "✅ No active alarms"
        
        critical = len([a for a in active_alarms if a.get("catname", "").lower() in ["critical", "high"]])
        summary = f"🚨 {len(active_alarms)} alarms"
        if critical > 0:
            summary += f" ({critical} critical)"
        
        return summary
    
    async def get_health_summary(self, site_name: str = "default") -> str:
        """Get concise health summary."""
        health = await self.get_site_health(site_name)
        if isinstance(health, dict) and "error" in health:
            return f"Error: {health['error']}"
        if not isinstance(health, list):
            return "Error: Unexpected response format"
        
        if not health:
            return "❓ No health data"
        
        healthy = len([h for h in health if h.get("status") == "ok"])
        total = len(health)
        
        if healthy == total:
            return f"✅ All systems OK ({total}/{total})"
        else:
            return f"⚠️ {healthy}/{total} systems OK"
    
    async def get_dashboard_summary(self, site_name: str = "default") -> str:
        """Get concise dashboard summary."""
        dashboard = await self.get_dashboard_metrics(site_name)
        if isinstance(dashboard, dict) and "error" in dashboard:
            return f"Error: {dashboard['error']}"
        
        # Handle both dict and list formats
        if isinstance(dashboard, list):
            if not dashboard:
                return "📊 No dashboard data"
            latest_data = dashboard[-1]
            wan_tx = latest_data.get("wan-tx_bytes", latest_data.get("tx_bytes-r", 0))
            wan_rx = latest_data.get("wan-rx_bytes", latest_data.get("rx_bytes-r", 0))
            total_traffic = wan_tx + wan_rx
            if total_traffic > 0:
                formatted_traffic = format_bytes(total_traffic)
                return f"📊 WAN traffic: {formatted_traffic}/s"
            return "📊 Dashboard active (no traffic)"
        elif isinstance(dashboard, dict):
            if "num_clients" in dashboard:
                return f"📊 {dashboard['num_clients']} clients active"
            return "📊 Dashboard active"
        else:
            return "📊 Dashboard data unavailable"