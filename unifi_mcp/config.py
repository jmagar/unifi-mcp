"""
Configuration and environment management for UniFi MCP Server.

Handles environment variables, logging configuration, and settings validation.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


class ClearingFileHandler(logging.FileHandler):
    """Custom file handler that clears the log file when it exceeds max_bytes."""
    
    def __init__(self, filename, max_bytes=10 * 1024 * 1024, mode='a', encoding=None, delay=False):
        """
        Initialize handler with file size limit.
        
        Args:
            filename: Log file path
            max_bytes: Maximum file size in bytes (default 10MB)
            mode: File open mode
            encoding: File encoding
            delay: Whether to delay file opening
        """
        self.max_bytes = max_bytes
        super().__init__(filename, mode, encoding, delay)
    
    def emit(self, record):
        """Emit a record, checking file size first."""
        try:
            # Check file size before writing
            if self.stream and hasattr(self.stream, 'name'):
                try:
                    file_size = os.path.getsize(self.stream.name)
                    if file_size >= self.max_bytes:
                        # Close current stream
                        if self.stream:
                            self.stream.close()
                        
                        # Clear the file by opening in write mode
                        with open(self.baseFilename, 'w') as f:
                            f.write("")  # Clear the file
                        
                        # Reopen in append mode
                        self.stream = self._open()
                        
                        # Log the clearing event
                        clear_msg = f"Log file cleared - exceeded {self.max_bytes / (1024*1024):.1f}MB limit"
                        super().emit(logging.LogRecord(
                            name="unifi_mcp.config",
                            level=logging.INFO,
                            pathname="",
                            lineno=0,
                            msg=clear_msg,
                            args=(),
                            exc_info=None
                        ))
                
                except (OSError, IOError):
                    # If we can't check file size, just continue
                    pass
            
            # Emit the original record
            super().emit(record)
            
        except Exception:
            # If anything goes wrong, fall back to standard behavior
            super().emit(record)


@dataclass
class UniFiConfig:
    """UniFi controller configuration settings."""
    
    # Required settings
    controller_url: str
    username: str
    password: str
    
    # Optional settings with defaults
    verify_ssl: bool = False
    is_udm_pro: bool = True
    
    @classmethod
    def from_env(cls) -> "UniFiConfig":
        """Create configuration from environment variables."""
        # Required settings
        controller_url = os.getenv("UNIFI_CONTROLLER_URL")
        username = os.getenv("UNIFI_USERNAME")
        password = os.getenv("UNIFI_PASSWORD")
        
        if not controller_url:
            raise ValueError("UNIFI_CONTROLLER_URL environment variable is required")
        if not username:
            raise ValueError("UNIFI_USERNAME environment variable is required")
        if not password:
            raise ValueError("UNIFI_PASSWORD environment variable is required")
        
        # Optional settings
        verify_ssl = os.getenv("UNIFI_VERIFY_SSL", "false").lower() == "true"
        is_udm_pro = os.getenv("UNIFI_IS_UDM_PRO", "true").lower() == "true"
        
        return cls(
            controller_url=controller_url,
            username=username,
            password=password,
            verify_ssl=verify_ssl,
            is_udm_pro=is_udm_pro
        )


@dataclass
class ServerConfig:
    """MCP server configuration settings."""
    
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create server configuration from environment variables."""
        host = os.getenv("UNIFI_LOCAL_MCP_HOST", "0.0.0.0")
        port = int(os.getenv("UNIFI_LOCAL_MCP_PORT", "8001"))
        log_level = os.getenv("UNIFI_LOCAL_MCP_LOG_LEVEL", "INFO")
        log_file = os.getenv("UNIFI_LOCAL_MCP_LOG_FILE")
        
        return cls(
            host=host,
            port=port,
            log_level=log_level,
            log_file=log_file
        )


def setup_logging(config: ServerConfig) -> None:
    """Configure logging based on server configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if specified
    if config.log_file:
        # Ensure log directory exists
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use our custom clearing file handler with 10MB limit
        file_handler = ClearingFileHandler(config.log_file, max_bytes=10 * 1024 * 1024)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("unifi_mcp").setLevel(getattr(logging, config.log_level.upper()))
    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_config() -> tuple[UniFiConfig, ServerConfig]:
    """Load both UniFi and server configurations from environment."""
    # Load .env file (same logic as original monolithic server)
    script_dir = Path(__file__).resolve().parent.parent  # Go up to project root
    env_file = script_dir / ".env"
    
    if env_file.exists():
        load_dotenv(env_file, override=True)
        logging.getLogger(__name__).debug(f"Loaded environment from {env_file}")
    
    unifi_config = UniFiConfig.from_env()
    server_config = ServerConfig.from_env()
    
    return unifi_config, server_config