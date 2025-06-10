# Unifi Site Manager MCP Server

This server provides an MCP interface to the Unifi Site Manager API (https://api.ui.com), allowing for programmatic interaction with your Unifi devices, sites, and configurations.

It defaults to **SSE (Server-Sent Events)** transport but can be configured for **STDIO**.

## Implemented Tools

1.  `list_hosts`: Retrieves all hosts (Unifi Consoles/Network Servers).
2.  `get_host_by_id`: Retrieves detailed information for a specific host.
3.  `list_sites`: Retrieves all sites.
4.  `list_devices`: Retrieves all UniFi devices, optionally filtered by host IDs.
5.  `get_isp_metrics`: Retrieves ISP metrics (5m or 1h intervals) for all sites.
6.  `query_isp_metrics`: Retrieves ISP metrics based on specific site queries.
7.  `list_sdwan_configs`: Retrieves all SD-WAN configurations.
8.  `get_sdwan_config_by_id`: Retrieves detailed information for a specific SD-WAN configuration.
9.  `get_sdwan_config_status`: Retrieves the deployment status of a specific SD-WAN configuration.

**Note on Pagination**: Tools that list multiple items (e.g., `list_hosts`, `list_sites`, `list_devices`) will automatically fetch and return all pages of results.

**Note on Early Access (EA) Endpoints**: `get_isp_metrics`, `query_isp_metrics`, `list_sdwan_configs`, `get_sdwan_config_by_id`, and `get_sdwan_config_status` use API endpoints currently marked as Early Access (`/ea/`) by Ubiquiti. These may be subject to change and have a lower rate limit (100 requests/minute) compared to v1 endpoints (10,000 requests/minute).

## Setup

### Prerequisites
- Python 3.8+ (Python 3.10+ recommended for the `yarr-mcp` project)
- An operational Unifi setup accessible via `api.ui.com` or a self-hosted controller.
- An API Key from [unifi.ui.com/api](https://unifi.ui.com/api).
- `uv` (recommended for package management within the `yarr-mcp` project).

### Installation

1.  **Clone the `yarr-mcp` repository (if you haven't already):**
    ```bash
    git clone https://github.com/jmagar/yarr-mcp.git
    cd yarr-mcp
    ```

2.  **Install dependencies:**
    Dependencies (`fastmcp`, `httpx`, `python-dotenv`) are managed by the main `yarr-mcp` project's `pyproject.toml`.
    Ensure you have activated the main project's virtual environment (e.g., using `uv venv`):
    ```bash
    # From the yarr-mcp project root
    source .venv/bin/activate 
    # or on Windows (Git Bash/WSL)
    # source .venv/Scripts/activate
    ```
    *Note: The local `src/unifi-mcp/requirements.txt` file is redundant if using the main project setup and can be ignored or removed.*

3.  **Set up environment variables:**
    Create or update a `.env` file in the `yarr-mcp` project root, or specifically in the `src/unifi-mcp/` directory (server-specific `.env` will override project root settings).
    Refer to `src/unifi-mcp/.env.example` for all available options. Key variables:

    ```env
    UNIFI_API_KEY="YOUR_ACTUAL_UNIFI_API_KEY"
    UNIFI_BASE_URL="https://api.ui.com" # Or your self-hosted controller URL
    
    UNIFI_MCP_TRANSPORT=sse
    UNIFI_MCP_HOST=0.0.0.0
    UNIFI_MCP_PORT=6969 # Default port for Unifi MCP
    UNIFI_MCP_LOG_LEVEL=INFO
    UNIFI_MCP_LOG_FILE=unifi_mcp.log 
    ```
    You can obtain your `UNIFI_API_KEY` from [unifi.ui.com/api](https://unifi.ui.com/api).

## Running the Server

Ensure your project's virtual environment is activated.

From the `yarr-mcp` project root, run:
```bash
python src/unifi-mcp/unifi-mcp-server.py
```

The server will start, by default using SSE transport on the host and port specified by `UNIFI_MCP_HOST` and `UNIFI_MCP_PORT` (defaults to `0.0.0.0:6969`). You should see log messages indicating the server has started and the SSE endpoint, e.g.:
`INFO - UnifiMCPServer - Unifi Site Manager MCP Server SSE endpoint will be available at http://0.0.0.0:6969/mcp`

## Client Configuration Examples

### Claude Desktop Configuration (for SSE)

If the server is running with SSE transport (the default), you can create an `MCP_CLIENT_CONFIG` JSON file to instruct Claude Desktop (or similar clients) how to connect. For example:

```json
{
  "clients": [
    {
      "name": "UnifiSiteManagerMCP", // Or any name you prefer
      "command": ["curl", "-N", "http://localhost:6969/mcp"],
      "type": "sse",
      "is_available": true
    }
    // Add other MCP server configurations here
  ]
}
```
Place this file (e.g., `mcp_config.json`) in a location your MCP client can access and configure the client to use it (often via an `MCP_CLIENT_CONFIG` environment variable pointing to this file's path).

### STDIO Transport Alternative
If you need to use STDIO transport, set `UNIFI_MCP_TRANSPORT=stdio` in your `.env` file. The `MCP_CLIENT_CONFIG` command would then be:
`["python", "/path/to/yarr-mcp/src/unifi-mcp/unifi-mcp-server.py"]` (using the absolute path to the script).

*Previous client examples for Cline and VS Code specific JSON files are still valid but Claude Desktop's generic MCP_CLIENT_CONFIG is preferred for broader compatibility.*

## Troubleshooting

-   **Authentication Errors**: Ensure `UNIFI_API_KEY` and `UNIFI_BASE_URL` are correct and the `.env` file is loaded.
-   **Connection Issues**: Check if the server is running and the port (`6969` by default) is not blocked.
-   **Rate Limiting**: If you encounter 429 errors, especially with EA endpoints, you might be hitting rate limits. The server attempts to respect `Retry-After` headers.
-   **Logs**: Check server logs in the console and in the file specified by `UNIFI_MCP_LOG_FILE` (default: `src/unifi-mcp/unifi_mcp.log`). # unifi-mcp
