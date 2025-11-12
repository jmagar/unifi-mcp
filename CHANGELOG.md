# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **CRITICAL**: Updated fastmcp from 2.12.0 to >=2.13.0 to fix Confused Deputy Account Takeover vulnerability
- Added MAC address format validation with regex to prevent malformed input
- Enhanced .gitignore to explicitly prevent .env file commits
- Added SECURITY.md with comprehensive security documentation
- Added mypy type checking configuration for improved type safety

### Fixed
- Fixed undefined variable `events` in monitoring_tools.py (should be `dpi_stats` and `rogue_aps`)
- Fixed missing `json` import in tests/conftest.py
- Fixed all ruff linting errors (31 total)
  - Removed unused imports (24 auto-fixed)
  - Removed unnecessary f-string prefixes
  - Cleaned up unused local variables
- Fixed type annotation issues
  - Added Optional types for None default parameters
  - Fixed return type annotation in BaseService.check_list_response
  - Added proper type hints throughout codebase

### Changed
- Enhanced run.sh script to work without uv package manager (falls back to python3)
- Improved error messages for MAC address validation failures
- Updated BaseService.normalize_mac to validate MAC address format

### Added
- Created mypy.ini for type checking configuration
- Added CHANGELOG.md for tracking changes
- Added comprehensive inline documentation for security practices
- Enhanced exception handling for MAC address validation

## [0.1.0] - Initial Release

### Added
- Modular MCP server architecture with FastMCP
- Support for UniFi OS devices (UDM Pro, Cloud Gateway Max)
- Support for legacy UniFi controllers
- Comprehensive device management tools
- Client management and control tools
- Network configuration access
- Monitoring and statistics tools
- Resource-based data access via unifi:// URIs
- Clean, formatted output for all tools and resources
- Docker support with docker-compose
- Advanced logging with log rotation
- Background server execution with PID file management
- Comprehensive test suite
- Health check endpoint

### Security
- Non-root Docker container execution
- Environment-based configuration
- No hardcoded credentials
- Proper async resource cleanup
- CSRF token support for UniFi OS
- Session management with automatic retry

[Unreleased]: https://github.com/jmagar/unifi-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jmagar/unifi-mcp/releases/tag/v0.1.0
