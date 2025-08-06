"""
MCP Resources for UniFi Controller data access.

This module provides all MCP resources for structured data access
using the unifi:// URI scheme.
"""

from .device_resources import register_device_resources
from .client_resources import register_client_resources
from .network_resources import register_network_resources
from .monitoring_resources import register_monitoring_resources
from .overview_resources import register_overview_resources
from .site_resources import register_site_resources

__all__ = [
    "register_device_resources",
    "register_client_resources",
    "register_network_resources", 
    "register_monitoring_resources",
    "register_overview_resources",
    "register_site_resources"
]