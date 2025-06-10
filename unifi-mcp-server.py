"""
MCP Server for Unifi Site Manager API
Implements the approved tool set using SSE transport.
Automatically handles pagination for list endpoints.
Built with FastMCP following best practices.
"""

import os
import sys
import httpx
import asyncio
# import time # Not strictly used, can be removed if no direct time.sleep calls remain
import logging
from logging.handlers import RotatingFileHandler # Added
from pathlib import Path # Added
from typing import Optional, List, Dict, Any, Tuple
from fastmcp import FastMCP
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# --- Ensure SCRIPT_DIR is on sys.path for imports ---
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# --- Environment Variable Loading ---
# Load .env from project root first, then override with server-specific .env if it exists
project_root_env = SCRIPT_DIR.parent.parent / ".env"
server_specific_env = SCRIPT_DIR / ".env"

if project_root_env.exists():
    load_dotenv(project_root_env, override=False)
if server_specific_env.exists():
    load_dotenv(server_specific_env, override=True)

# --- Configuration ---
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY")
UNIFI_BASE_URL = os.getenv("UNIFI_BASE_URL", "https://api.ui.com").rstrip('/')

UNIFI_MCP_TRANSPORT = os.getenv("UNIFI_MCP_TRANSPORT", "sse").lower()
UNIFI_MCP_HOST = os.getenv("UNIFI_MCP_HOST", "0.0.0.0")
UNIFI_MCP_PORT = int(os.getenv("UNIFI_MCP_PORT", "6969"))
UNIFI_MCP_LOG_LEVEL = os.getenv("UNIFI_MCP_LOG_LEVEL", "INFO").upper()
UNIFI_MCP_LOG_FILE = os.getenv("UNIFI_MCP_LOG_FILE", "unifi_mcp.log")

# --- Logger Setup ---
NUMERIC_LOG_LEVEL = getattr(logging, UNIFI_MCP_LOG_LEVEL, logging.INFO)

logger = logging.getLogger("UnifiMCPServer") # Specific logger name
logger.setLevel(NUMERIC_LOG_LEVEL)
logger.propagate = False # Prevent duplicate logs if root logger is configured

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(NUMERIC_LOG_LEVEL)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File Handler
try:
    log_file_path = SCRIPT_DIR / UNIFI_MCP_LOG_FILE
    file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(NUMERIC_LOG_LEVEL)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.info(f"Logging initialized (console and file: {log_file_path}). Log level: {UNIFI_MCP_LOG_LEVEL}")
except Exception as e:
    logger.warning(f"Could not initialize file logging to {log_file_path}: {e}. Console logging only.")
    logger.info(f"Logging initialized (console only). Log level: {UNIFI_MCP_LOG_LEVEL}")

logger.info(f"UNIFI_MCP_TRANSPORT: {UNIFI_MCP_TRANSPORT}, HOST: {UNIFI_MCP_HOST}, PORT: {UNIFI_MCP_PORT}")
logger.info(f"UNIFI_BASE_URL: {UNIFI_BASE_URL}")
logger.info(f"UNIFI_API_KEY: {'****' + UNIFI_API_KEY[-4:] if UNIFI_API_KEY and len(UNIFI_API_KEY) > 4 else 'Not Set or Too Short'}")


# --- Critical Checks ---
if not UNIFI_API_KEY:
    logger.error("CRITICAL: UNIFI_API_KEY environment variable not set. Server cannot function.")
    sys.exit(1)
if not UNIFI_BASE_URL:
    logger.error("CRITICAL: UNIFI_BASE_URL environment variable not set. Server cannot function.")
    sys.exit(1)

# --- API Client Helper ---

async def _make_api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    is_paginated: bool = False
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Helper function to make authenticated API requests with error handling and rate limiting."""
    if not UNIFI_API_KEY:
        raise ValueError("API Key is not configured.")

    if not endpoint.startswith('/'):
        endpoint = f"/{endpoint}"
    
    url = f"{UNIFI_BASE_URL}{endpoint}"
    
    default_headers = {
        "X-API-Key": UNIFI_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json" if json_data else "application/x-www-form-urlencoded",
    }
    if headers:
        default_headers.update(headers)

    all_data = []
    next_page_params = params.copy() if params else {}

    async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for potentially long calls
        while True:
            try:
                logger.info(f"Requesting {method} {url} with params: {next_page_params}")
                response = await client.request(
                    method,
                    url,
                    params=next_page_params,
                    json=json_data,
                    headers=default_headers
                )
                
                # Handle Rate Limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5")) # Default to 5s wait
                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    continue # Retry the same request

                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                response_json = response.json()

                # Check for API-level errors even with 200 OK
                if response_json.get("httpStatusCode", 200) >= 400:
                     logger.error(f"API Error ({response_json.get('httpStatusCode')}): {response_json.get('code')} - {response_json.get('message')}")
                     # You might want to raise a specific exception here
                     raise httpx.HTTPStatusError(
                         message=f"API Error: {response_json.get('message')}", 
                         request=response.request, 
                         response=response
                     )

                data = response_json.get("data")

                if not is_paginated:
                    return data # Return immediately if not paginated

                if isinstance(data, list):
                    all_data.extend(data)
                elif isinstance(data, dict):
                     # Handle cases like query_isp_metrics where 'data' is an object containing 'metrics' list
                     if 'metrics' in data and isinstance(data['metrics'], list):
                         all_data.extend(data['metrics'])
                     elif data: # If it's just a single object result wrapped in 'data'
                         return data 
                     else: # No relevant data found
                          logger.warning(f"Unexpected data structure in paginated response for {url}: {data}")
                          return all_data # Return what we have so far
                else:
                    logger.warning(f"Unexpected data type in paginated response for {url}: {type(data)}")
                    return all_data # Return what we have so far or handle appropriately


                next_token = response_json.get("nextToken")
                if next_token:
                    logger.info(f"Fetching next page with token: {next_token}")
                    next_page_params["nextToken"] = next_token
                    # Remove pageSize if present, as nextToken implies continuation
                    next_page_params.pop("pageSize", None) 
                else:
                    break # Exit loop if no next token

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                # Attempt to parse error response from Unifi API structure
                try:
                    error_details = e.response.json()
                    raise Exception(f"API Call Failed ({error_details.get('httpStatusCode')}): {error_details.get('code')} - {error_details.get('message', e.response.text)}")
                except Exception as parse_err:
                    logger.error(f"Could not parse error response: {parse_err}")
                    raise e # Re-raise original HTTP error if parsing fails
            except httpx.RequestError as e:
                logger.error(f"Request error occurred: {e}")
                raise e
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                raise e

    logger.info(f"Finished fetching all pages for {method} {url}. Total items: {len(all_data)}")
    return all_data


# --- MCP Server Definition ---

mcp = FastMCP(
    name="Unifi Site Manager MCP",
    instructions="""Provides tools to interact with the Unifi Site Manager API (api.ui.com).
    Handles authentication using the UNIFI_API_KEY environment variable.
    Automatically fetches all pages for list operations.
    Use caution with Early Access (EA) endpoints (ISP Metrics, SD-WAN).""",
)

# --- MCP Tools ---

@mcp.tool()
async def list_hosts(
    page_size: Optional[int] = 50, # Sensible default page size
) -> List[Dict[str, Any]]:
    """Retrieves ALL hosts (Unifi Consoles/Network Servers) associated with the UI account. Automatically handles pagination."""
    params = {}
    if page_size:
        params["pageSize"] = str(page_size) # API expects string
    return await _make_api_request("GET", "/v1/hosts", params=params, is_paginated=True)

@mcp.tool()
async def get_host_by_id(host_id: str) -> Dict[str, Any]:
    """Retrieves detailed information for a specific host by its ID."""
    if not host_id:
        raise ValueError("host_id is required.")
    return await _make_api_request("GET", f"/v1/hosts/{host_id}")

@mcp.tool()
async def list_sites(
    page_size: Optional[int] = 50
) -> List[Dict[str, Any]]:
    """Retrieves ALL sites associated with the UI account. Automatically handles pagination."""
    params = {}
    if page_size:
        params["pageSize"] = str(page_size)
    return await _make_api_request("GET", "/v1/sites", params=params, is_paginated=True)

@mcp.tool()
async def list_devices(
    host_ids: Optional[List[str]] = None,
    time: Optional[str] = None,
    page_size: Optional[int] = 50
) -> List[Dict[str, Any]]:
    """Retrieves ALL UniFi devices, optionally filtered by host IDs and time. Automatically handles pagination."""
    params = {}
    if host_ids:
        params["hostIds[]"] = host_ids # httpx handles list params correctly
    if time:
        params["time"] = time
    if page_size:
        params["pageSize"] = str(page_size)
        
    # Note: The API returns data grouped by host. The pagination seems to be across hosts/responses,
    # not strictly devices. We aggregate the 'devices' lists from each host object returned by the API.
    raw_host_data = await _make_api_request("GET", "/v1/devices", params=params, is_paginated=True)
    
    all_devices = []
    for host_entry in raw_host_data:
        if 'devices' in host_entry and isinstance(host_entry['devices'], list):
            # Add hostId to each device for context
            for device in host_entry['devices']:
                 device['hostId'] = host_entry.get('hostId')
                 device['hostName'] = host_entry.get('hostName')
            all_devices.extend(host_entry['devices'])
            
    return all_devices


@mcp.tool()
async def get_isp_metrics(
    metric_type: str, # '5m' or '1h'
    begin_timestamp: Optional[str] = None,
    end_timestamp: Optional[str] = None,
    duration: Optional[str] = None # e.g., '24h', '7d', '30d'
) -> List[Dict[str, Any]]:
    """(Early Access) Retrieves ISP metrics for all sites. Specify '5m' or '1h' for metric_type. Use either duration OR timestamp range."""
    if metric_type not in ['5m', '1h']:
        raise ValueError("metric_type must be '5m' or '1h'.")
    if duration and (begin_timestamp or end_timestamp):
        raise ValueError("Cannot use 'duration' together with 'begin_timestamp' or 'end_timestamp'.")

    params = {}
    if begin_timestamp:
        params["beginTimestamp"] = begin_timestamp
    if end_timestamp:
        params["endTimestamp"] = end_timestamp
    if duration:
        params["duration"] = duration
        
    return await _make_api_request("GET", f"/ea/isp-metrics/{metric_type}", params=params)


@mcp.tool()
async def query_isp_metrics(
    metric_type: str, # '5m' or '1h'
    sites_query: List[Dict[str, str]] # List of {"siteId": "...", "hostId": "...", "beginTimestamp": "...", "endTimestamp": "..."}
) -> Dict[str, Any]:
    """(Early Access) Retrieves ISP metrics based on specific site queries. sites_query is a list of dictionaries, each specifying siteId, hostId, and optional timestamps."""
    if metric_type not in ['5m', '1h']:
        raise ValueError("metric_type must be '5m' or '1h'.")
    if not sites_query:
        raise ValueError("sites_query list cannot be empty.")
    
    # API expects {"sites": [...]} in the body
    request_body = {"sites": sites_query}
    
    # This endpoint's successful response puts the metrics list inside data.metrics
    # _make_api_request handles extracting from data.metrics if needed, but returns the whole 'data' object
    # including status: partialSuccess if present.
    return await _make_api_request("POST", f"/ea/isp-metrics/{metric_type}/query", json_data=request_body)


@mcp.tool()
async def list_sdwan_configs() -> List[Dict[str, Any]]:
    """(Early Access) Retrieves a list of all SD-WAN configurations."""
    return await _make_api_request("GET", "/ea/sd-wan-configs")


@mcp.tool()
async def get_sdwan_config_by_id(config_id: str) -> Dict[str, Any]:
    """Retrieves details for a specific SD-WAN configuration by its ID (EA)."""
    if not config_id:
        raise ValueError("config_id is required.")
    return await _make_api_request("GET", f"/ea/sdwan/configs/{config_id}")


@mcp.tool()
async def get_sdwan_config_status(config_id: str) -> Dict[str, Any]:
    """Retrieves the status for a specific SD-WAN configuration by its ID (EA)."""
    if not config_id:
        raise ValueError("config_id is required.")
    return await _make_api_request("GET", f"/ea/sdwan/configs/{config_id}/status")

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting Unifi Site Manager MCP Server...")
    
    if UNIFI_MCP_TRANSPORT == 'sse':
        mcp.run(
            transport='sse',
            host=UNIFI_MCP_HOST,
            port=UNIFI_MCP_PORT,
            path='/mcp'  # Standardized path for MCP over SSE
        )
    elif UNIFI_MCP_TRANSPORT == 'stdio':
        mcp.run() # Defaults to stdio
    else:
        logger.error(f"Invalid UNIFI_MCP_TRANSPORT: '{UNIFI_MCP_TRANSPORT}'. Must be 'sse' or 'stdio'. Defaulting to STDIO.")
        mcp.run()
    logger.info("Unifi Site Manager MCP Server stopped.") 