#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${CLAUDE_PLUGIN_ROOT}/.env"
BACKUP_DIR="${CLAUDE_PLUGIN_ROOT}/backups"
mkdir -p "$BACKUP_DIR"

declare -A MANAGED=(
  [UNIFI_URL]="${CLAUDE_PLUGIN_OPTION_UNIFI_URL:-}"
  [UNIFI_USERNAME]="${CLAUDE_PLUGIN_OPTION_UNIFI_USERNAME:-}"
  [UNIFI_PASSWORD]="${CLAUDE_PLUGIN_OPTION_UNIFI_PASSWORD:-}"
  [UNIFI_MCP_TOKEN]="${CLAUDE_PLUGIN_OPTION_UNIFI_MCP_TOKEN:-}"
)

touch "$ENV_FILE"

(
  flock 9
  if [ -s "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${BACKUP_DIR}/.env.bak.$(date +%s)"
  fi

  for key in "${!MANAGED[@]}"; do
    value="${MANAGED[$key]}"
    [ -z "$value" ] && continue
    if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
      awk -v k="$key" -v v="$value" \
        'BEGIN{FS="="; OFS="="} $1==k {$2=v; print; next} {print}' \
        "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
    else
      echo "${key}=${value}" >> "$ENV_FILE"
    fi
  done

  if ! grep -q "^UNIFI_MCP_TOKEN=" "$ENV_FILE" 2>/dev/null; then
    echo "sync-env: UNIFI_MCP_TOKEN is not set — set UNIFI_MCP_TOKEN in plugin userConfig" >&2
    exit 1
  fi

  chmod 600 "$ENV_FILE"

  mapfile -t baks < <(ls -t "${BACKUP_DIR}"/.env.bak.* 2>/dev/null || true)
  for bak in "${baks[@]}"; do chmod 600 "$bak"; done
  for bak in "${baks[@]:3}"; do rm -f "$bak"; done
) 9>"/tmp/unifi-sync-env.lock"
