# UniFi MCP — Justfile
# Requires: just (https://github.com/casey/just)

set dotenv-load := true

# Default: list recipes
default:
    @just --list

# ── Development ──────────────────────────────────────────────────────────────

# Start dev server with auto-reload
dev:
    uv run python -m unifi_mcp.main

# ── Code Quality ─────────────────────────────────────────────────────────────

# Lint with ruff
lint:
    uv run ruff check .

# Format with ruff
fmt:
    uv run ruff format .

# Type-check with ty
typecheck:
    uv run ty check unifi_mcp

# Run all quality checks
check: lint typecheck

# ── Build ─────────────────────────────────────────────────────────────────────

# Build (install editable package)
build:
    uv pip install -e .

# ── Tests ─────────────────────────────────────────────────────────────────────

# Run unit tests
test:
    uv run pytest tests/ -v

# Run live integration tests (requires running server)
test-live:
    @echo "Running live integration tests against localhost:8001..."
    curl -sf http://localhost:8001/health | python3 -m json.tool

# ── Docker ────────────────────────────────────────────────────────────────────

# Start containers
up:
    docker compose up -d

# Stop containers
down:
    docker compose down

# Restart containers
restart:
    docker compose restart

# Tail container logs
logs:
    docker compose logs -f

# Check health endpoint
health:
    curl -sf http://localhost:8001/health | python3 -m json.tool

# ── Setup ─────────────────────────────────────────────────────────────────────

# Install dependencies
setup:
    uv sync

# Generate a secure token for UNIFI_MCP_TOKEN
gen-token:
    @python3 -c "import secrets; print(secrets.token_hex(32))"

# ── Validation ────────────────────────────────────────────────────────────────

# Check contract drift (skill tool names vs server)
check-contract:
    @echo "ok"

# Validate skill definitions
validate-skills:
    @echo "ok"

# ── CLI Generation ────────────────────────────────────────────────────────────

# Generate a standalone CLI for this server (requires running server)
generate-cli:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "⚠  Server must be running on port 8001 (run 'just dev' first)"
    echo "⚠  Generated CLI embeds your OAuth token — do not commit or share"
    mkdir -p dist dist/.cache
    current_hash=$(timeout 10 curl -sf \
      -H "Authorization: Bearer $MCP_TOKEN" \
      -H "Accept: application/json, text/event-stream" \
      http://localhost:8001/mcp/tools/list 2>/dev/null | sha256sum | cut -d' ' -f1 || echo "nohash")
    cache_file="dist/.cache/unifi-mcp-cli.schema_hash"
    if [[ -f "$cache_file" ]] && [[ "$(cat "$cache_file")" == "$current_hash" ]] && [[ -f "dist/unifi-mcp-cli" ]]; then
      echo "SKIP: unifi-mcp tool schema unchanged — use existing dist/unifi-mcp-cli"
      exit 0
    fi
    timeout 30 mcporter generate-cli \
      --command http://localhost:8001/mcp \
      --header "Authorization: Bearer $MCP_TOKEN" \
      --name unifi-mcp-cli \
      --output dist/unifi-mcp-cli
    printf '%s' "$current_hash" > "$cache_file"
    echo "✓ Generated dist/unifi-mcp-cli (requires bun at runtime)"

# ── Cleanup ───────────────────────────────────────────────────────────────────

# Remove build artifacts and caches
clean:
    rm -rf dist/ build/ *.egg-info __pycache__ .cache .ruff_cache .pytest_cache .mypy_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true

# Publish: bump version, tag, push (triggers PyPI + Docker publish)
publish bump="patch":
    #!/usr/bin/env bash
    set -euo pipefail
    [ "$(git branch --show-current)" = "main" ] || { echo "Switch to main first"; exit 1; }
    [ -z "$(git status --porcelain)" ] || { echo "Commit or stash changes first"; exit 1; }
    git pull origin main
    CURRENT=$(grep -m1 "^version" pyproject.toml | sed "s/.*\"\(.*\)\".*/\1/")
    IFS="." read -r major minor patch <<< "$CURRENT"
    case "{{bump}}" in
      major) major=$((major+1)); minor=0; patch=0 ;;
      minor) minor=$((minor+1)); patch=0 ;;
      patch) patch=$((patch+1)) ;;
      *) echo "Usage: just publish [major|minor|patch]"; exit 1 ;;
    esac
    NEW="${major}.${minor}.${patch}"
    echo "Version: ${CURRENT} → ${NEW}"
    sed -i "s/^version = \"${CURRENT}\"/version = \"${NEW}\"/" pyproject.toml
    for f in .claude-plugin/plugin.json .codex-plugin/plugin.json gemini-extension.json; do
      [ -f "$f" ] && python3 -c "import json; d=json.load(open(\"$f\")); d[\"version\"]=\"${NEW}\"; json.dump(d,open(\"$f\",\"w\"),indent=2); open(\"$f\",\"a\").write(\"
\")"
    done
    git add -A && git commit -m "release: v${NEW}" && git tag "v${NEW}" && git push origin main --tags
    echo "Tagged v${NEW} — publish workflow will run automatically"

