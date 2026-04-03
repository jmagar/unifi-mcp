# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Modular UniFi MCP server using FastMCP with streamable HTTP transport. Built as a Python package (`unifi_mcp`) with organized tools, resources, client, and configuration modules. Connects directly to local UniFi controllers (Cloud Gateway Max, UDM Pro) for real-time device management.

### Package Structure
- `unifi_mcp/main.py` - Main entry point
- `unifi_mcp/server.py` - FastMCP server implementation  
- `unifi_mcp/client.py` - UniFi controller client
- `unifi_mcp/tools/` - MCP tool implementations
- `unifi_mcp/resources/` - MCP resource implementations
- `unifi_mcp/config.py` - Configuration and logging setup

## Development Commands

```bash
# Setup and run
uv sync              # Install dependencies
./run.sh             # Start server in background with log streaming
./run.sh logs        # Stream logs from running server

# Development
uv add package-name                    # Add dependency
uv run ruff check .                   # Lint code
uv run mypy .                         # Type check
uv run pytest                        # Run tests
uv run python -m unifi_mcp.main      # Run server directly
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
- **Tools**: Expose the unified `unifi` tool plus `unifi_help`, not dozens of top-level tools
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
- `UNIFI_URL` - Full URL with port (https://IP:443 or https://IP:8443)
- `UNIFI_USERNAME` - Local admin account (not UniFi Cloud)
- `UNIFI_PASSWORD` - Local admin password
- `UNIFI_MCP_TOKEN` - Bearer token for HTTP auth unless `UNIFI_MCP_NO_AUTH=true`

Optional logging and server management:
- `UNIFI_MCP_HOST` - Bind host (default: `0.0.0.0`)
- `UNIFI_MCP_PORT` - HTTP port (default: `8001`)
- `UNIFI_MCP_LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `UNIFI_MCP_LOG_FILE` - Server-specific log file setting
- `UNIFI_MCP_NO_AUTH` - Disable bearer auth for trusted local testing only

Default settings handle most UDM Pro/Cloud Gateway Max setups.

## Testing MCP Server

```bash
# Test via HTTP API
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'
```

Server runs on port 8001 with endpoint `/mcp`.

## Logging and Process Management

The server includes advanced logging and process management features:

### Log Management
- **Prettified logs**: Colored output with timestamps via `./run.sh`
- **Background execution**: Server runs independently in background
- **PID file management**: Process ID stored for easy management
- **Log streaming**: Use `./run.sh logs` to view logs from running server

### Log Colors
- **DEBUG**: Cyan
- **INFO**: Green  
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Magenta

### Process Control
```bash
./run.sh              # Start server + stream logs
./run.sh logs         # Stream logs only
kill $(cat logs/unifi-mcp.pid)  # Stop server
```


## Version Bumping

**Every feature branch push MUST bump the version in ALL version-bearing files.**

Bump type is determined by the commit message prefix:
- `feat!:` or `BREAKING CHANGE` → **major** (X+1.0.0)
- `feat` or `feat(...)` → **minor** (X.Y+1.0)
- Everything else (`fix`, `chore`, `refactor`, `test`, `docs`, etc.) → **patch** (X.Y.Z+1)

**Files to update (if they exist in this repo):**
- `Cargo.toml` — `version = "X.Y.Z"` in `[package]`
- `package.json` — `"version": "X.Y.Z"`
- `pyproject.toml` — `version = "X.Y.Z"` in `[project]`
- `.claude-plugin/plugin.json` — `"version": "X.Y.Z"`
- `.codex-plugin/plugin.json` — `"version": "X.Y.Z"`
- `gemini-extension.json` — `"version": "X.Y.Z"`

All files MUST have the same version. Never bump only one file.
