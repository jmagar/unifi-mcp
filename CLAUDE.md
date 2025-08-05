# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Single-file UniFi MCP server in `unifi-local-mcp-server.py` using FastMCP with streamable HTTP transport. Connects directly to local UniFi controllers (Cloud Gateway Max, UDM Pro) for real-time device management.

## Development Commands

```bash
# Setup and run
uv sync              # Install dependencies
./run.sh             # Start server (syncs deps + runs server)

# Development
uv add package-name                    # Add dependency
uv run ruff check .                   # Lint code
uv run mypy .                         # Type check
uv run pytest                        # Run tests
```

## Key Architecture Patterns

### Authentication Flow
- UDM Pro/UniFi OS: `/api/auth/login` → TOKEN cookie → JWT CSRF token
- Legacy controllers: `/api/login` → unifises cookie → header CSRF
- Always call `await ensure_authenticated()` before API operations

### Data Formatting
- All byte values auto-converted to human readable (KB, MB, GB) via `format_data_values()`
- Raw values preserved as `*_raw` fields
- Apply to all tool responses with bandwidth/storage data

### MCP Patterns
- **Tools**: Use `@mcp.tool()` for operations (get_devices, restart_device)
- **Resources**: Use `@mcp.resource("unifi://path")` for data access
- **Default site**: All operations default to "default" site when site_name omitted
- **Return objects**: Resources return data objects, not JSON strings

## Critical Implementation Details

### MAC Address Handling
Always normalize: `mac.lower().replace("-", ":").replace(".", ":")`

### Site Parameters
- Use `site_name=""` for `/self/sites` endpoint only
- Use `site_name="default"` for all other site-specific operations
- Most tools/resources default to "default" site

### Error Handling
- Return error objects `{"error": "message"}` instead of raising exceptions
- Log authentication failures with URL for debugging
- Handle MFA gracefully (return false, log available methods)

### Controller Type Detection
`UNIFI_IS_UDM_PRO=true` changes:
- API base path: `/proxy/network/api` vs `/api`
- Login endpoint: `/api/auth/login` vs `/api/login`
- Cookie name: `TOKEN` vs `unifises`

## Configuration Requirements

Required environment variables:
- `UNIFI_CONTROLLER_URL` - Full URL with port (https://IP:443 or https://IP:8443)
- `UNIFI_USERNAME` - Local admin account (not UniFi Cloud)
- `UNIFI_PASSWORD` - Local admin password

Default settings handle most UDM Pro/Cloud Gateway Max setups.

## Testing MCP Server

```bash
# Test via HTTP API
curl -X POST http://localhost:8001/mcp/call -H "Content-Type: application/json" -d '{"method": "tools/call", "params": {"name": "get_devices"}}'
```

Server runs on port 8001 with endpoint `/mcp`.