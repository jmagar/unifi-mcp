#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${CLAUDE_PLUGIN_ROOT}/.env"
BACKUP_DIR="${CLAUDE_PLUGIN_ROOT}/backups"
mkdir -p "$BACKUP_DIR"

declare -A MANAGED=(
  [UNIFI_CONTROLLER_URL]="${CLAUDE_PLUGIN_OPTION_UNIFI_CONTROLLER_URL:-}"
  [UNIFI_USERNAME]="${CLAUDE_PLUGIN_OPTION_UNIFI_USERNAME:-}"
  [UNIFI_PASSWORD]="${CLAUDE_PLUGIN_OPTION_UNIFI_PASSWORD:-}"
  [UNIFI_MCP_URL]="${CLAUDE_PLUGIN_OPTION_UNIFI_MCP_URL:-}"
)

touch "$ENV_FILE"

if [ -s "$ENV_FILE" ]; then
  cp "$ENV_FILE" "${BACKUP_DIR}/.env.bak.$(date +%s)"
fi

for key in "${!MANAGED[@]}"; do
  value="${MANAGED[$key]}"
  [ -z "$value" ] && continue
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
done

chmod 600 "$ENV_FILE"

mapfile -t baks < <(ls -t "${BACKUP_DIR}"/.env.bak.* 2>/dev/null)
for bak in "${baks[@]}"; do
  chmod 600 "$bak"
done
for bak in "${baks[@]:3}"; do
  rm -f "$bak"
done
