# Connect to MCP

How to connect to the unifi-mcp server from every supported client and transport.

## Claude Code Plugin (Recommended)

```bash
/plugin marketplace add jmagar/unifi-mcp
```

Enter credentials when prompted. The plugin connects to the HTTP endpoint configured in `unifi_mcp_url` (default: `https://unifi.tootie.tv/mcp`).

## Claude Desktop (stdio)

Add to `~/.config/claude-desktop/config.json` (Linux) or `~/Library/Application Support/Claude Desktop/config.json` (macOS):

```json
{
  "mcpServers": {
    "unifi-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "unifi_mcp.main"],
      "cwd": "/path/to/unifi-mcp",
      "env": {
        "UNIFI_URL": "https://192.168.1.1:443",
        "UNIFI_USERNAME": "admin",
        "UNIFI_PASSWORD": "your_password",
        "UNIFI_MCP_TRANSPORT": "stdio",
        "UNIFI_MCP_NO_AUTH": "true"
      }
    }
  }
}
```

## Claude Code (.mcp.json)

For project-local configuration, add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "unifi-mcp": {
      "type": "http",
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

## Codex CLI

```bash
codex --mcp "http://localhost:8001/mcp" --mcp-header "Authorization: Bearer $UNIFI_MCP_TOKEN"
```

Or configure in `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "unifi-mcp": {
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

## curl (Manual Testing)

```bash
# Health check (no auth)
curl -sf http://localhost:8001/health | python3 -m json.tool

# Tool call
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'

# Help tool
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi_help","arguments":{}}}'
```

## PyPI Package (uvx)

Install from PyPI and run via stdio:

```bash
uvx mcp-unifi
```

Set environment variables for controller credentials.

## See Also

- [TRANSPORT.md](TRANSPORT.md) — Transport details
- [AUTH.md](AUTH.md) — Authentication requirements
- [DEPLOY.md](DEPLOY.md) — Deployment options
