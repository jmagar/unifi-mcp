"""
Tests for UniFi MCP configuration module.

Following FastMCP testing patterns for configuration validation and management.
"""

import pytest
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch
from inline_snapshot import snapshot

from unifi_mcp.config import (
    UniFiConfig, ServerConfig, 
    ClearingFileHandler, setup_logging
)


class TestUniFiConfig:
    """Test UniFi configuration data class."""
    
    def test_unifi_config_creation_basic(self):
        """Test basic UniFi config creation."""
        config = UniFiConfig(
            controller_url="https://192.168.1.1:443",
            username="admin", 
            password="password123"
        )
        
        assert config.controller_url == "https://192.168.1.1:443"
        assert config.username == "admin"
        assert config.password == "password123"
        assert config.verify_ssl is False  # Default
        assert config.is_udm_pro is True  # Default


    def test_unifi_config_creation_with_all_options(self):
        """Test UniFi config creation with all options specified."""
        config = UniFiConfig(
            controller_url="https://192.168.1.1:8443",
            username="admin",
            password="password123", 
            verify_ssl=True,
            is_udm_pro=False
        )
        
        assert config.controller_url == "https://192.168.1.1:8443"
        assert config.verify_ssl is True
        assert config.is_udm_pro is False


    def test_unifi_config_from_env_complete(self):
        """Test UniFi config creation from environment variables."""
        env_vars = {
            "UNIFI_CONTROLLER_URL": "https://test.local:443",
            "UNIFI_USERNAME": "testuser",
            "UNIFI_PASSWORD": "testpass",
            "UNIFI_VERIFY_SSL": "true", 
            "UNIFI_IS_UDM_PRO": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = UniFiConfig.from_env()
            
            assert config.controller_url == "https://test.local:443"
            assert config.username == "testuser"
            assert config.password == "testpass"
            assert config.verify_ssl is True
            assert config.is_udm_pro is False


    def test_unifi_config_from_env_missing_required(self):
        """Test UniFi config creation with missing required env vars."""
        # Clear environment
        env_vars = {
            "UNIFI_CONTROLLER_URL": "",
            "UNIFI_USERNAME": "",
            "UNIFI_PASSWORD": ""
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="environment variable is required"):
                UniFiConfig.from_env()


    def test_unifi_config_from_env_defaults(self):
        """Test UniFi config creation with only required env vars set."""
        env_vars = {
            "UNIFI_CONTROLLER_URL": "https://192.168.1.1:443",
            "UNIFI_USERNAME": "admin",
            "UNIFI_PASSWORD": "password"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = UniFiConfig.from_env()
            
            # Should use defaults for optional values
            assert config.verify_ssl is False
            assert config.is_udm_pro is True


    def test_unifi_config_boolean_parsing(self):
        """Test boolean value parsing from environment variables."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("1", False),  # Only "true" variants work in actual implementation
            ("yes", False),  # Only "true" variants work in actual implementation
            ("0", False),
            ("no", False),
            ("", False),
            ("invalid", False)
        ]
        
        for env_value, expected in test_cases:
            env_vars = {
                "UNIFI_CONTROLLER_URL": "https://test.local",
                "UNIFI_USERNAME": "admin",
                "UNIFI_PASSWORD": "password",
                "UNIFI_VERIFY_SSL": env_value
            }
            
            with patch.dict(os.environ, env_vars, clear=True):
                config = UniFiConfig.from_env()
                assert config.verify_ssl is expected, f"Failed for value: {env_value}"


    def test_unifi_config_validation_url_format(self):
        """Test URL format validation."""
        # Valid URLs should work
        valid_urls = [
            "https://192.168.1.1:443",
            "https://unifi.local:8443",
            "https://10.0.0.1:443"
        ]
        
        for url in valid_urls:
            config = UniFiConfig(
                controller_url=url,
                username="admin",
                password="password"
            )
            assert config.controller_url == url


class TestServerConfig:
    """Test server configuration data class."""
    
    def test_server_config_creation_defaults(self):
        """Test server config creation with defaults."""
        config = ServerConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8001
        assert config.log_level == "INFO"
        assert config.log_file is None


    def test_server_config_creation_custom(self):
        """Test server config creation with custom values."""
        config = ServerConfig(
            host="127.0.0.1",
            port=9000,
            log_level="DEBUG",
            log_file="/tmp/test.log"
        )
        
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.log_level == "DEBUG"
        assert config.log_file == "/tmp/test.log"


    def test_server_config_from_env(self):
        """Test server config creation from environment variables."""
        env_vars = {
            "UNIFI_LOCAL_MCP_HOST": "192.168.1.100",
            "UNIFI_LOCAL_MCP_PORT": "8002",
            "UNIFI_LOCAL_MCP_LOG_LEVEL": "ERROR",
            "UNIFI_LOCAL_MCP_LOG_FILE": "/var/log/unifi-mcp.log"
        }
        
        with patch.dict(os.environ, env_vars):
            config = ServerConfig.from_env()
            
            assert config.host == "192.168.1.100"
            assert config.port == 8002
            assert config.log_level == "ERROR"
            assert config.log_file == "/var/log/unifi-mcp.log"


    def test_server_config_from_env_defaults(self):
        """Test server config from env with missing values uses defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig.from_env()
            
            assert config.host == "0.0.0.0"
            assert config.port == 8001
            assert config.log_level == "INFO"
            assert config.log_file is None


    def test_server_config_port_validation(self):
        """Test server config port validation."""
        # Valid ports
        valid_ports = [1, 80, 8001, 9000, 65535]
        
        for port in valid_ports:
            config = ServerConfig(port=port)
            assert config.port == port
            
        # Invalid port should raise ValueError
        with pytest.raises(ValueError):
            ServerConfig(port=0)
            
        with pytest.raises(ValueError):
            ServerConfig(port=65536)


class TestClearingFileHandler:
    """Test custom clearing file handler."""
    
    def test_clearing_file_handler_creation(self):
        """Test creation of clearing file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            handler = ClearingFileHandler(
                temp_file.name,
                max_bytes=1024
            )
            
            assert handler.max_bytes == 1024
            assert handler.baseFilename == temp_file.name
            
            # Cleanup
            handler.close()
            os.unlink(temp_file.name)


    def test_clearing_file_handler_size_limit(self):
        """Test file clearing when size limit is reached."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write initial content to exceed limit
            temp_file.write(b"x" * 2000)  # 2KB
            temp_file.flush()
            
            handler = ClearingFileHandler(
                temp_file.name,
                max_bytes=1024  # 1KB limit
            )
            
            # Create a test record
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="Test message", args=(), exc_info=None
            )
            
            # Emit the record - should trigger file clearing
            handler.emit(record)
            
            # Check file was cleared and new content written
            handler.flush()
            with open(temp_file.name, 'r') as f:
                content = f.read()
                assert len(content) < 1024  # Should be much smaller now
                assert "Test message" in content
            
            # Cleanup
            handler.close()
            os.unlink(temp_file.name)


class TestLoggingSetup:
    """Test logging setup functions."""
    
    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        config = ServerConfig(log_level="INFO")
        
        setup_logging(config)
        
        # Should set root logger level
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.INFO


    def test_setup_logging_with_file(self):
        """Test logging setup with file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            config = ServerConfig(
                log_level="DEBUG",
                log_file=temp_file.name
            )
            
            setup_logging(config)
            
            # Test logging to file
            logger = logging.getLogger("test_logger")
            logger.info("Test message")
            
            # Check message was written to file
            with open(temp_file.name, 'r') as f:
                content = f.read()
                assert "Test message" in content
            
            # Cleanup
            os.unlink(temp_file.name)


    def test_setup_logging_level_validation(self):
        """Test logging level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            config = ServerConfig(log_level=level)
            setup_logging(config)  # Should not raise
            
            # Verify level was set correctly
            root_logger = logging.getLogger()
            expected_level = getattr(logging, level)
            assert root_logger.level <= expected_level


class TestConfigIntegration:
    """Test configuration integration scenarios."""
    
    def test_config_snapshot_structure(self):
        """Test config structure using snapshots."""
        config = UniFiConfig(
            controller_url="https://192.168.1.1:443",
            username="admin",
            password="password123"
        )
        
        config_dict = {
            "controller_url": config.controller_url,
            "username": config.username,
            "verify_ssl": config.verify_ssl,
            "is_udm_pro": config.is_udm_pro
        }
        
        assert config_dict == snapshot({
            "controller_url": "https://192.168.1.1:443",
            "username": "admin",
            "verify_ssl": False,
            "is_udm_pro": True
        })


    def test_server_config_snapshot_structure(self):
        """Test server config structure using snapshots."""
        config = ServerConfig()
        
        config_dict = {
            "host": config.host,
            "port": config.port,
            "log_level": config.log_level,
            "log_file": config.log_file
        }
        
        assert config_dict == snapshot({
            "host": "0.0.0.0",
            "port": 8001,
            "log_level": "INFO",
            "log_file": None
        })


    def test_combined_config_initialization(self):
        """Test initialization with both config types."""
        unifi_config = UniFiConfig(
            controller_url="https://test.local",
            username="admin",
            password="password"
        )
        
        server_config = ServerConfig(
            host="127.0.0.1",
            port=8000
        )
        
        # Should be able to use both together
        assert unifi_config.controller_url == "https://test.local"
        assert server_config.host == "127.0.0.1"
        
        # Different instances should be independent
        assert unifi_config.verify_ssl is False
        assert server_config.port == 8000


@pytest.mark.integration  
class TestConfigIntegrationTests:
    """Integration tests for configuration with real environment."""
    
    def test_config_from_real_environment(self):
        """Test config creation from actual environment variables."""
        # Only run if we have real environment variables
        controller_url = os.getenv("UNIFI_CONTROLLER_URL")
        username = os.getenv("UNIFI_USERNAME")
        password = os.getenv("UNIFI_PASSWORD")
        
        if not all([controller_url, username, password]):
            pytest.skip("Real environment variables not available")
        
        try:
            config = UniFiConfig.from_env()
            
            assert config.controller_url == controller_url
            assert config.username == username
            assert config.password == password
            
            # Should have valid values
            assert isinstance(config.verify_ssl, bool)
            assert isinstance(config.is_udm_pro, bool)
            
        except ValueError as e:
            pytest.fail(f"Failed to create config from environment: {e}")