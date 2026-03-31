#!/usr/bin/env bash
set -euo pipefail

GITIGNORE="${CLAUDE_PLUGIN_ROOT}/.gitignore"

REQUIRED=(
  ".env"
  ".env.*"
  "!.env.example"
  "backups/*"
  "!backups/.gitkeep"
  "logs/*"
  "!logs/.gitkeep"
)

if [ "${1:-}" = "--check" ]; then
  missing=()
  for pattern in "${REQUIRED[@]}"; do
    if ! grep -qxF "$pattern" "$GITIGNORE" 2>/dev/null; then
      missing+=("$pattern")
    fi
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "ensure-ignore-files: missing patterns in .gitignore:" >&2
    for p in "${missing[@]}"; do
      echo "  $p" >&2
    done
    exit 1
  fi
  exit 0
fi

touch "$GITIGNORE"

for pattern in "${REQUIRED[@]}"; do
  if ! grep -qxF "$pattern" "$GITIGNORE" 2>/dev/null; then
    echo "$pattern" >> "$GITIGNORE"
  fi
done
