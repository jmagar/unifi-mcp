# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/jmagar/unifi-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jmagar/unifi-mcp/releases/tag/v0.1.0
