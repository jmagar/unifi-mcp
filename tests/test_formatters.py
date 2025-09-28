"""
Tests for UniFi MCP formatters module.

Following FastMCP testing patterns for data formatting functionality.
"""

import pytest
from inline_snapshot import snapshot

from unifi_mcp.formatters import (
    format_bytes, format_timestamp, format_uptime,
    format_device_summary, format_client_summary, format_site_summary,
    format_devices_list, format_clients_list, format_data_values
)


class TestBytesFormatting:
    """Test byte value formatting functions."""
    
    def test_format_bytes_basic_values(self):
        """Test basic byte formatting with common values."""
        assert format_bytes(0) == "0 B"
        assert format_bytes(1) == "1 B"
        assert format_bytes(1023) == "1023 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"  # 1.5 * 1024
        

    def test_format_bytes_larger_values(self):
        """Test byte formatting with larger values."""
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.0 TB"
        assert format_bytes(1024 * 1024 * 1024 * 1024 * 1024) == "1.0 PB"


    def test_format_bytes_precision(self):
        """Test byte formatting precision."""
        assert format_bytes(1500) == "1.5 KB"
        assert format_bytes(2500000) == "2.4 MB"
        assert format_bytes(3500000000) == "3.3 GB"


    def test_format_bytes_edge_cases(self):
        """Test byte formatting edge cases."""
        assert format_bytes(None) == "0 B"
        assert format_bytes(-1) == "-1 B"  # Actual implementation doesn't handle negatives specially
        assert format_bytes("invalid") == "0 B"


class TestTimestampFormatting:
    """Test timestamp formatting functions."""
    
    def test_format_timestamp_unix_epoch(self):
        """Test timestamp formatting with Unix epoch values."""
        # Test known timestamp (2024-01-01 00:00:00 UTC = 2023-12-31 19:00:00 EST)
        timestamp = 1704067200
        result = format_timestamp(timestamp)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "2023" in result  # Will be 2023 in EST timezone


    def test_format_timestamp_edge_cases(self):
        """Test timestamp formatting edge cases."""
        assert format_timestamp(0) == "1969-12-31 19:00:00"  # EST timezone
        assert format_timestamp(None) == "Unknown"
        assert format_timestamp("invalid") == "Unknown"
        assert format_timestamp(-1) == "1969-12-31 18:59:59"  # -1 second from epoch


class TestUptimeFormatting:
    """Test uptime formatting functions."""
    
    def test_format_uptime_seconds(self):
        """Test uptime formatting for values in seconds."""
        assert format_uptime(30) == "Less than 1 minute"
        assert format_uptime(59) == "Less than 1 minute"


    def test_format_uptime_minutes(self):
        """Test uptime formatting for values in minutes."""
        assert format_uptime(60) == "1 minute"
        assert format_uptime(90) == "1 minute"  # Rounds to nearest minute
        assert format_uptime(3599) == "59 minutes"


    def test_format_uptime_hours(self):
        """Test uptime formatting for values in hours."""
        assert format_uptime(3600) == "1 hour"
        assert format_uptime(3661) == "1 hour, 1 minute"
        assert format_uptime(7200) == "2 hours"


    def test_format_uptime_days(self):
        """Test uptime formatting for values in days."""
        assert format_uptime(86400) == "1 day"
        assert format_uptime(90000) == "1 day, 1 hour"
        assert format_uptime(172800) == "2 days"


    def test_format_uptime_edge_cases(self):
        """Test uptime formatting edge cases."""
        assert format_uptime(0) == "Less than 1 minute"
        assert format_uptime(None) == "Unknown"
        assert format_uptime(-1) == "Less than 1 minute"
        assert format_uptime("invalid") == "Unknown"


class TestDeviceFormatting:
    """Test device summary formatting."""
    
    def test_format_device_summary_switch(self):
        """Test device formatting for switch devices."""
        device_data = {
            "_id": "device1",
            "name": "Main Switch",
            "mac": "aa:bb:cc:dd:ee:01",
            "model": "US-24-250W",
            "type": "usw",
            "state": 1,
            "ip": "192.168.1.10",
            "uptime": 86400,
            "bytes": 1000000000,
            "rx_bytes": 500000000,
            "tx_bytes": 500000000,
            "cpu": 15.5,
            "mem": 45.2,
            "temperature": 42.1
        }
        
        result = format_device_summary(device_data)
        
        assert result["name"] == "Main Switch"
        assert result["model"] == "US-24-250W"
        assert result["type"] == "switch"
        assert result["status"] == "online"
        assert result["ip"] == "192.168.1.10"
        assert result["uptime"] == "1d"
        assert "GB" in result["total_bytes"]
        assert result["cpu_percentage"] == 15.5
        assert result["memory_percentage"] == 45.2


    def test_format_device_summary_access_point(self):
        """Test device formatting for access point devices."""
        device_data = {
            "_id": "device2",
            "name": "Living Room AP", 
            "mac": "aa:bb:cc:dd:ee:02",
            "model": "U6-Pro",
            "type": "uap",
            "state": 1,
            "ip": "192.168.1.11",
            "uptime": 43200,
            "bytes": 2000000000,
            "radio_table": [
                {"name": "wifi0", "channel": 36, "tx_power": 20},
                {"name": "wifi1", "channel": 6, "tx_power": 17}
            ]
        }
        
        result = format_device_summary(device_data)
        
        assert result["name"] == "Living Room AP"
        assert result["type"] == "access_point"
        assert result["status"] == "online"
        assert "wifi_radios" in result
        assert len(result["wifi_radios"]) == 2


    def test_format_device_summary_offline_device(self):
        """Test device formatting for offline devices."""
        device_data = {
            "_id": "device3",
            "name": "Offline Switch",
            "mac": "aa:bb:cc:dd:ee:03", 
            "model": "US-8-60W",
            "type": "usw",
            "state": 0,  # Offline
            "ip": "192.168.1.12"
        }
        
        result = format_device_summary(device_data)
        
        assert result["name"] == "Offline Switch"
        assert result["status"] == "offline"
        assert result["uptime"] == "0s"


class TestClientFormatting:
    """Test client summary formatting."""
    
    def test_format_client_summary_wireless(self):
        """Test client formatting for wireless clients."""
        client_data = {
            "_id": "client1",
            "name": "John's iPhone",
            "mac": "aa:bb:cc:dd:ee:f1",
            "ip": "192.168.1.100",
            "hostname": "Johns-iPhone",
            "is_online": True,
            "is_wired": False,
            "ap_mac": "aa:bb:cc:dd:ee:02",
            "essid": "HomeWiFi",
            "channel": 36,
            "signal": -45,
            "rx_bytes": 1000000,
            "tx_bytes": 2000000,
            "uptime": 7200,
            "satisfaction": 95
        }
        
        result = format_client_summary(client_data)
        
        assert result["name"] == "John's iPhone"
        assert result["status"] == "online"
        assert result["connection_type"] == "wireless"
        assert result["wifi_network"] == "HomeWiFi"
        assert result["signal_strength"] == -45
        assert result["satisfaction"] == 95
        assert "MB" in result["total_bytes"]


    def test_format_client_summary_wired(self):
        """Test client formatting for wired clients."""
        client_data = {
            "_id": "client2",
            "name": "Desktop PC",
            "mac": "aa:bb:cc:dd:ee:f2",
            "ip": "192.168.1.101",
            "hostname": "desktop-pc", 
            "is_online": True,
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:01",
            "sw_port": 1,
            "rx_bytes": 5000000,
            "tx_bytes": 3000000,
            "uptime": 25200
        }
        
        result = format_client_summary(client_data)
        
        assert result["name"] == "Desktop PC"
        assert result["connection_type"] == "wired"
        assert result["switch_port"] == 1
        assert "signal_strength" not in result
        assert "wifi_network" not in result


class TestSiteFormatting:
    """Test site summary formatting."""
    
    def test_format_site_summary_basic(self):
        """Test basic site formatting."""
        site_data = {
            "_id": "site1",
            "name": "default",
            "desc": "Default Site",
            "role": "admin",
            "num_new_alarms": 2,
            "health": [
                {"subsystem": "wan", "status": "ok"},
                {"subsystem": "lan", "status": "ok"},
                {"subsystem": "wlan", "status": "warning"}
            ]
        }
        
        result = format_site_summary(site_data)
        
        assert result["name"] == "default"
        assert result["description"] == "Default Site"
        assert result["role"] == "admin"
        assert result["new_alarms"] == 2
        assert len(result["health_status"]) == 3
        assert result["health_status"]["wan"] == "ok"
        assert result["health_status"]["wlan"] == "warning"


class TestListFormatting:
    """Test list formatting functions."""
    
    def test_format_devices_list(self, mock_device_data):
        """Test devices list formatting."""
        result = format_devices_list(mock_device_data)
        
        assert isinstance(result, str)
        assert "Main Switch" in result
        assert "Living Room AP" in result
        assert "online" in result.lower()


    def test_format_clients_list(self, mock_client_data):
        """Test clients list formatting."""
        result = format_clients_list(mock_client_data)
        
        assert isinstance(result, str)
        assert "John's iPhone" in result
        assert "Desktop PC" in result
        assert "online" in result.lower()


class TestDataValuesFormatting:
    """Test data values formatting function."""
    
    def test_format_data_values_device(self):
        """Test data values formatting for device data."""
        data = {
            "name": "Test Device",
            "bytes": 1000000000,
            "rx_bytes": 500000000,
            "tx_bytes": 500000000,
            "port_table": [
                {"rx_bytes": 100000000, "tx_bytes": 200000000},
                {"rx_bytes": 300000000, "tx_bytes": 100000000}
            ],
            "uptime": 86400,
            "other_field": "unchanged"
        }
        
        result = format_data_values(data)
        
        # Should format byte values
        assert "GB" in result["bytes_formatted"]
        assert "MB" in result["rx_bytes_formatted"] 
        assert "MB" in result["tx_bytes_formatted"]
        
        # Should preserve raw values
        assert result["bytes_raw"] == 1000000000
        assert result["rx_bytes_raw"] == 500000000
        
        # Should format nested byte values
        assert "MB" in result["port_table"][0]["rx_bytes_formatted"]
        
        # Should leave other fields unchanged
        assert result["other_field"] == "unchanged"


    def test_format_data_values_snapshot(self):
        """Test data values formatting structure with snapshots."""
        data = {
            "bytes": 1073741824,  # 1 GB
            "uptime": 3661  # 1h 1m 1s
        }
        
        result = format_data_values(data)
        
        assert result == snapshot({
            "bytes": 1073741824,
            "bytes_raw": 1073741824,
            "bytes_formatted": "1.0 GB",
            "uptime": 3661,
            "uptime_raw": 3661,
            "uptime_formatted": "1h 1m 1s"
        })


class TestFormattingErrorHandling:
    """Test error handling in formatting functions."""
    
    def test_format_device_summary_missing_fields(self):
        """Test device formatting with missing required fields."""
        incomplete_device = {"_id": "device1"}
        
        result = format_device_summary(incomplete_device)
        
        # Should handle missing fields gracefully
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "Unknown Device"


    def test_format_client_summary_missing_fields(self):
        """Test client formatting with missing required fields."""
        incomplete_client = {"_id": "client1"}
        
        result = format_client_summary(incomplete_client)
        
        # Should handle missing fields gracefully
        assert isinstance(result, dict)
        assert "name" in result


    def test_format_data_values_with_none_values(self):
        """Test data formatting with None values."""
        data = {
            "bytes": None,
            "uptime": None,
            "valid_field": "test"
        }
        
        result = format_data_values(data)
        
        # Should handle None values gracefully
        assert result["valid_field"] == "test"
        assert "bytes_formatted" in result
        assert result["bytes_formatted"] == "0 B"