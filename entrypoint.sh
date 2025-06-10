#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.

echo "UniFi MCP Service: Initializing..."

# Validate required environment variables
if [ -z "$UNIFI_BASE_URL" ]; then
    echo "Error: UNIFI_BASE_URL environment variable is required"
    exit 1
fi

if [ -z "$UNIFI_API_KEY" ]; then
    echo "Error: UNIFI_API_KEY environment variable is required"
    exit 1
fi

# Set defaults for MCP server configuration
export UNIFI_MCP_HOST=${UNIFI_MCP_HOST:-"0.0.0.0"}
export UNIFI_MCP_PORT=${UNIFI_MCP_PORT:-"9155"}
export UNIFI_MCP_TRANSPORT=${UNIFI_MCP_TRANSPORT:-"sse"}
export UNIFI_LOG_LEVEL=${UNIFI_LOG_LEVEL:-"INFO"}

echo "UniFi MCP Service: Configuration validated"
echo "  - UNIFI_BASE_URL: $UNIFI_BASE_URL"
echo "  - UNIFI_API_KEY: ***SET***"
echo "  - MCP_HOST: $UNIFI_MCP_HOST"
echo "  - MCP_PORT: $UNIFI_MCP_PORT"
echo "  - MCP_TRANSPORT: $UNIFI_MCP_TRANSPORT"
echo "  - LOG_LEVEL: $UNIFI_LOG_LEVEL"

# Change to app directory (important for relative path handling)
cd /app

echo "UniFi MCP Service: Starting server..."
exec python3 unifi-mcp-server.py 