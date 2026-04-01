#!/usr/bin/env bash
set -euo pipefail

GITIGNORE="${CLAUDE_PLUGIN_ROOT}/.gitignore"
DOCKERIGNORE="${CLAUDE_PLUGIN_ROOT}/.dockerignore"

GITIGNORE_REQUIRED=(
  ".env"
  ".env.*"
  "!.env.example"
  "backups/*"
  "!backups/.gitkeep"
  "logs/*"
  "!logs/.gitkeep"
)

DOCKERIGNORE_REQUIRED=(
  ".env"
  ".env.*"
  "backups/"
  "logs/"
)

check_file() {
  local file="$1"
  local label="$2"
  shift 2
  local missing=()
  local pattern

  for pattern in "$@"; do
    if ! grep -qxF "$pattern" "$file" 2>/dev/null; then
      missing+=("$pattern")
    fi
  done

  if [ ${#missing[@]} -gt 0 ]; then
    echo "ensure-ignore-files: missing patterns in ${label}:" >&2
    for pattern in "${missing[@]}"; do
      echo "  ${pattern}" >&2
    done
    return 1
  fi
}

ensure_file() {
  local file="$1"
  shift
  local pattern

  touch "$file"
  for pattern in "$@"; do
    if ! grep -qxF "$pattern" "$file" 2>/dev/null; then
      echo "$pattern" >> "$file"
    fi
  done
}

if [ "${1:-}" = "--check" ]; then
  check_file "$GITIGNORE" ".gitignore" "${GITIGNORE_REQUIRED[@]}"
  check_file "$DOCKERIGNORE" ".dockerignore" "${DOCKERIGNORE_REQUIRED[@]}"
  exit 0
fi

ensure_file "$GITIGNORE" "${GITIGNORE_REQUIRED[@]}"
ensure_file "$DOCKERIGNORE" "${DOCKERIGNORE_REQUIRED[@]}"
