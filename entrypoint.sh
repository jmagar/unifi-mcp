#!/bin/sh
set -eu
: "${UNIFI_MCP_TOKEN:?UNIFI_MCP_TOKEN must be set}"
exec "$@"
