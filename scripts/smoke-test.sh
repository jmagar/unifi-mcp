#!/usr/bin/env bash
# smoke-test.sh — Live end-to-end smoke test for unifi-mcp
# Tests both MCP tools via mcporter with strict PASS/FAIL validation.
# Exit code 0 = all passed. Exit code 1 = one or more failures.
#
# Usage:
#   bash scripts/smoke-test.sh [--url http://host:8001/mcp]
#   bash scripts/smoke-test.sh --config path/to/mcporter.json
#
# Requirements: mcporter, curl, python3

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
MCP_URL="${UNIFI_MCP_URL:-http://localhost:8001/mcp}"
HEALTH_URL="${MCP_URL%/mcp}/health"
MCPORTER_CONFIG="config/mcporter.json"
_MCPORTER_CONFIG_TMPFILE=""

# Clean up temp config on exit
trap '[[ -n "$_MCPORTER_CONFIG_TMPFILE" ]] && rm -f "$_MCPORTER_CONFIG_TMPFILE"' EXIT

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            [[ -z "${2:-}" ]] && { echo "Error: --url requires a value"; exit 1; }
            MCP_URL="$2"; HEALTH_URL="${MCP_URL%/mcp}/health"; shift 2
            # Create a temp mcporter config pointing at the custom URL so both
            # health checks and mcporter tool calls target the same server.
            _MCPORTER_CONFIG_TMPFILE=$(mktemp /tmp/mcporter-XXXXXX.json)
            printf '{"mcpServers":{"unifi":{"url":"%s","transport":"http"}}}' "$MCP_URL" > "$_MCPORTER_CONFIG_TMPFILE"
            MCPORTER_CONFIG="$_MCPORTER_CONFIG_TMPFILE"
            ;;
        --config)
            [[ -z "${2:-}" ]] && { echo "Error: --config requires a value"; exit 1; }
            MCPORTER_CONFIG="$2"; shift 2
            ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ─── Helpers ─────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
ERRORS=()

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'
COLOR_BOLD='\033[1m'

pass() { echo -e "${COLOR_GREEN}PASS${COLOR_RESET}  $1"; (( PASS++ )) || true; }
fail() { echo -e "${COLOR_RED}FAIL${COLOR_RESET}  $1"; ERRORS+=("$1"); (( FAIL++ )) || true; }

# Run mcporter call and return output (exits non-zero on tool error)
mcp_call() {
    local tool="$1"; shift
    mcporter call --config "$MCPORTER_CONFIG" "unifi.${tool}" "$@" 2>&1
}

# Extract JSON field from output
json_get() {
    local json="$1" field="$2"
    echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d$field)" 2>/dev/null
}

# Assert a JSON field equals expected value
assert_eq() {
    local label="$1" actual="$2" expected="$3"
    if [[ "$actual" == "$expected" ]]; then
        pass "$label"
    else
        fail "$label (expected '$expected', got '$actual')"
    fi
}

# Assert JSON output represents a successful MCP tool call (isError absent or false)
assert_no_error() {
    local label="$1" output="$2"
    if echo "$output" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    sys.exit(1 if d.get('isError') else 0)
except (json.JSONDecodeError, ValueError):
    # Non-JSON output is a real failure — mcporter/tool returned garbage
    sys.exit(1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
        pass "$label"
    else
        local detail
        detail=$(echo "$output" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    content = d.get('content', [])
    print(content[0].get('text','')[:120] if content else '')
except Exception:
    print(sys.stdin.read()[:120])
" 2>/dev/null)
        fail "$label (isError=true: $detail)"
    fi
}

# Assert output contains non-empty text content
assert_has_content() {
    local label="$1" output="$2"
    local text_len
    text_len=$(echo "$output" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    content = d.get('content', [])
    total = sum(len(c.get('text','')) for c in content)
    print(total)
except Exception:
    print(0)
" 2>/dev/null || echo "0")
    if [[ "$text_len" -gt 0 ]]; then
        pass "$label"
    else
        fail "$label (empty content)"
    fi
}

# ─── Phase 1: Pre-flight ─────────────────────────────────────────────────────
echo ""
echo -e "${COLOR_BOLD}=== unifi-mcp smoke test ===${COLOR_RESET}"
echo "MCP URL: $MCP_URL"
echo ""

echo -e "${COLOR_BOLD}[1/3] Pre-flight checks${COLOR_RESET}"

# 1a: Health endpoint
HEALTH=$(curl -sf "$HEALTH_URL" 2>&1) || { echo -e "${COLOR_RED}ABORT${COLOR_RESET}  Health endpoint unreachable: $HEALTH_URL"; exit 1; }
HEALTH_STATUS=$(json_get "$HEALTH" "['status']")
assert_eq "Health endpoint responds" "$HEALTH_STATUS" "ok"

# 1b: mcporter can reach server and lists all 2 tools
TOOL_LIST=$(mcporter list unifi --config "$MCPORTER_CONFIG" 2>&1)
TOOL_COUNT=$(echo "$TOOL_LIST" | grep -c "^  function " || true)
if [[ "$TOOL_COUNT" -eq 2 ]]; then
    pass "mcporter lists 2 tools ($TOOL_COUNT found)"
else
    fail "mcporter tool count (expected 2, got $TOOL_COUNT)"
fi

# ─── Phase 2: Tool tests ─────────────────────────────────────────────────────
echo ""
echo -e "${COLOR_BOLD}[2/3] Tool tests (read-only)${COLOR_RESET}"

# ── Tool 1: unifi_help ──────────────────────────────────────────────────────
echo ""
echo "Tool: unifi_help"
HELP=$(mcp_call unifi_help 2>&1)
assert_no_error "unifi_help: no error" "$HELP"
assert_has_content "unifi_help: returns non-empty help" "$HELP"

# ── Tool 2: unifi (action=get_controller_status) ────────────────────────────
echo ""
echo "Tool: unifi (get_controller_status)"
CONTROLLER=$(mcp_call unifi "action=get_controller_status" 2>&1)
assert_no_error "unifi(get_controller_status): no error" "$CONTROLLER"

# ── Tool 3: unifi (action=get_sites) ────────────────────────────────────────
echo ""
echo "Tool: unifi (get_sites)"
SITES=$(mcp_call unifi "action=get_sites" 2>&1)
assert_no_error "unifi(get_sites): no error" "$SITES"

# ── Tool 4: unifi (action=get_devices) ──────────────────────────────────────
echo ""
echo "Tool: unifi (get_devices)"
DEVICES=$(mcp_call unifi "action=get_devices" 2>&1)
assert_no_error "unifi(get_devices): no error" "$DEVICES"
assert_has_content "unifi(get_devices): returns device data" "$DEVICES"

# ── Tool 5: unifi (action=get_clients) ──────────────────────────────────────
echo ""
echo "Tool: unifi (get_clients)"
CLIENTS=$(mcp_call unifi "action=get_clients" 2>&1)
assert_no_error "unifi(get_clients): no error" "$CLIENTS"

# ─── Phase 3: Summary ────────────────────────────────────────────────────────
echo ""
echo -e "${COLOR_BOLD}[3/3] Results${COLOR_RESET}"
echo "─────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo -e "  Passed:  ${COLOR_GREEN}${PASS}${COLOR_RESET} / ${TOTAL}"
echo -e "  Failed:  ${COLOR_RED}${FAIL}${COLOR_RESET} / ${TOTAL}"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo -e "${COLOR_RED}Failures:${COLOR_RESET}"
    for e in "${ERRORS[@]}"; do
        echo "  - $e"
    done
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
    echo -e "${COLOR_GREEN}${COLOR_BOLD}ALL TESTS PASSED${COLOR_RESET}"
    exit 0
else
    echo -e "${COLOR_RED}${COLOR_BOLD}SMOKE TEST FAILED — $FAIL test(s) failed${COLOR_RESET}"
    exit 1
fi
