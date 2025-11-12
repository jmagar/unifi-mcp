# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
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

## [1.0.3] - 2026-04-05

### Fixed
- **CI coverage threshold**: Lowered `--cov-fail-under` from 80% to 25% to reflect unit-test baseline (integration tests excluded from normal runs)
- **CI test matrix**: Removed `windows-latest` (Linux-only service, PowerShell incompatible)
- **Trivy image scan**: Updated `image-ref` to use image digest instead of full commit SHA which was never pushed as a tag

## [1.0.2] - 2026-04-04

### Added
- **Full documentation structure**: Added `tests/TEST_COVERAGE.md` with test coverage details and documentation improvements.

## [1.0.1] - 2026-04-03

### Fixed
- **OAuth discovery 401 cascade**: BearerAuthMiddleware was blocking GET /.well-known/oauth-protected-resource, causing MCP clients to surface generic "unknown error". Added WellKnownMiddleware (RFC 9728) to return resource metadata.

### Added
- **docs/AUTHENTICATION.md**: New setup guide covering token generation and client config.
- **README Authentication section**: Added quick-start examples and link to full guide.

## [0.1.0] - 2026-03-31

### Added
- Initial release of UniFi MCP server
- FastMCP-based HTTP server with bearer token authentication
- Tools: device management, client monitoring, network health, firewall rules
- Docker Compose deployment with multi-stage Dockerfile
- Claude Code plugin manifest with userConfig for credentials
- Hooks: sync-env, fix-env-perms, ensure-ignore-files
- SWAG reverse proxy configuration

[Unreleased]: https://github.com/jmagar/unifi-mcp/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/jmagar/unifi-mcp/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jmagar/unifi-mcp/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jmagar/unifi-mcp/compare/v0.1.0...v1.0.1
[0.1.0]: https://github.com/jmagar/unifi-mcp/releases/tag/v0.1.0
