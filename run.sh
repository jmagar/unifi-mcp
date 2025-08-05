#!/bin/bash

# UniFi MCP Server (Modular Version) Startup Script

echo "Starting UniFi MCP Server (modular version)..."

# Sync dependencies
echo "Syncing dependencies..."
uv sync

# Run the modular server
echo "Starting server..."
uv run python -m unifi_mcp.main