# Logging and Error Handling

Logging and error handling patterns for unifi-mcp.

## Log Configuration

Logging is configured via `setup_logging()` in `config.py`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UNIFI_MCP_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `UNIFI_MCP_LOG_FILE` | `/tmp/unifi-mcp.log` | Log file path |

### Log Format

```
2026-04-04 12:00:00,000 - unifi_mcp.server - INFO - Initializing UniFi MCP Server...
```

Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Handlers

Two handlers are always configured:

1. **Console handler** — writes to stderr
2. **File handler** — writes to `UNIFI_MCP_LOG_FILE`

### File Handler Auto-Clear

The `ClearingFileHandler` automatically clears the log file when it exceeds 10 MB. This prevents disk exhaustion on long-running servers.

### Logger Levels

| Logger | Level |
|--------|-------|
| `unifi_mcp` | Configured level |
| `fastmcp` | WARNING |
| `urllib3` | WARNING |

FastMCP and urllib3 are set to WARNING to reduce noise from framework internals.

## Error Handling

### Service Layer

All services use `BaseService.create_error_result()` for consistent error responses:

```python
return ToolResult(
    content=[TextContent(type="text", text=f"Error: {message}")],
    structured_content={"error": message, "raw": raw_data}
)
```

### API Errors

API errors are caught at multiple levels:

1. **Client level**: `_make_request()` catches HTTP errors and returns `{"error": "..."}` dicts
2. **Service level**: Each service checks for error dicts before processing
3. **Server level**: The unified tool wraps everything in try/except

### Authentication Errors

On 401 response from the UniFi controller:
1. The client marks `is_authenticated = False`
2. Calls `authenticate()` to get a new session
3. Retries the original request once
4. Returns error if the retry also fails

### Response Validation

`BaseService.validate_response()` checks for:
- Error dict with `"error"` key
- UniFi API response code (`meta.rc != "ok"`)

`BaseService.check_list_response()` validates:
- Response is a list (not an error dict)
- Returns `ToolResult` error if invalid

### Response Size Cap

Responses exceeding 512 KB are truncated by `_truncate_response()`:

```python
MAX_RESPONSE_SIZE = 512 * 1024  # 512 KB
```

Truncated responses end with `\n... [truncated]`.

## Debug Mode

Set `UNIFI_MCP_LOG_LEVEL=DEBUG` to enable verbose logging:

- All API request URLs
- Authentication flow details
- CSRF token extraction
- Response parsing

Do not enable DEBUG in production — it may log request/response bodies that contain sensitive data.

## See Also

- [ENV.md](ENV.md) — Environment variables
- [DEPLOY.md](DEPLOY.md) — Deployment with logging
