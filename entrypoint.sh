#!/bin/sh
set -eu

no_auth="${UNIFI_MCP_NO_AUTH:-false}"
if [ -z "${UNIFI_MCP_TOKEN:-}" ] && [ "$no_auth" != "true" ] && [ "$no_auth" != "1" ]; then
  echo "UNIFI_MCP_TOKEN must be set unless UNIFI_MCP_NO_AUTH=true" >&2
  exit 1
fi

exec "$@"
