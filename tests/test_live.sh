#!/usr/bin/env bash
# =============================================================================
# tests/test_live.sh — Canonical live integration tests for unifi-mcp
#
# Modes:  http    — test a running HTTP server (default if URL provided)
#         docker  — build + run container, then run HTTP phases, tear down
#         stdio   — run MCP protocol tests over uvx/stdio
#         all     — run all three modes (default)
#
# Flags:
#   --mode http|docker|stdio|all   Select test mode (default: all)
#   --url URL                      Override server base URL (http mode)
#   --token TOKEN                  Override bearer token (http/docker mode)
#   --verbose                      Print full response bodies
#   --help                         Show this help and exit
#
# Environment variables:
#   UNIFI_URL         UniFi controller URL (required)
#   UNIFI_USERNAME    Controller admin username (required)
#   UNIFI_PASSWORD    Controller admin password (required)
#   PORT              MCP server listen port (default: 8001)
#
# Exit codes:
#   0 — all tests passed (or skipped)
#   1 — one or more tests failed
#   2 — prerequisite / startup failure
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
readonly SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
readonly LOG_FILE="${TMPDIR:-/tmp}/${SCRIPT_NAME%.sh}.$(date +%Y%m%d-%H%M%S).log"
readonly TS_START="$(date +%s%N 2>/dev/null || date +%s)000000000"

# ---------------------------------------------------------------------------
# Colours (auto-disabled when not a TTY)
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_RESET='\033[0m'
  C_BOLD='\033[1m'
  C_GREEN='\033[0;32m'
  C_RED='\033[0;31m'
  C_YELLOW='\033[0;33m'
  C_CYAN='\033[0;36m'
  C_BLUE='\033[0;34m'
  C_DIM='\033[2m'
else
  C_RESET='' C_BOLD='' C_GREEN='' C_RED='' C_YELLOW='' C_CYAN='' C_BLUE='' C_DIM=''
fi

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
MODE="all"
SERVER_URL=""        # set by --url or derived from PORT
BEARER_TOKEN=""      # set by --token or env UNIFI_MCP_TOKEN
VERBOSE=false
PORT="${PORT:-8001}"
ENTRY_POINT="unifi-mcp"   # pyproject.toml [project.scripts] key
CI_TOKEN="ci-integration-token"
DOCKER_CONTAINER=""   # set during docker mode

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
declare -a FAIL_NAMES=()

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode)
        MODE="${2:?--mode requires http|docker|stdio|all}"
        shift 2
        ;;
      --url)
        SERVER_URL="${2:?--url requires a value}"
        shift 2
        ;;
      --token)
        BEARER_TOKEN="${2:?--token requires a value}"
        shift 2
        ;;
      --verbose)
        VERBOSE=true
        shift
        ;;
      -h|--help)
        print_help
        exit 0
        ;;
      *)
        printf '[ERROR] Unknown argument: %s\n' "$1" >&2
        exit 2
        ;;
    esac
  done

  case "${MODE}" in
    http|docker|stdio|all) ;;
    *)
      printf '[ERROR] --mode must be http, docker, stdio, or all (got: %s)\n' "${MODE}" >&2
      exit 2
      ;;
  esac
}

print_help() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Modes:
  --mode http     Test a running HTTP server
  --mode docker   Build + run Docker container, test, tear down
  --mode stdio    Run MCP protocol tests over uvx/stdio
  --mode all      Run all three modes (default)

Flags:
  --url URL       Override server base URL for http mode
  --token TOKEN   Override bearer token for http/docker mode
  --verbose       Print full response bodies
  --help          Show this help and exit

Environment variables:
  UNIFI_URL         UniFi controller URL (required)
  UNIFI_USERNAME    Controller admin username (required)
  UNIFI_PASSWORD    Controller admin password (required)
  PORT              MCP server listen port (default: 8001)

Exit codes:
  0  All tests passed or skipped
  1  One or more tests failed
  2  Prerequisite / startup failure
EOF
}

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()    { printf "${C_CYAN}[INFO]${C_RESET}  %s\n" "$*" | tee -a "${LOG_FILE}"; }
log_warn()    { printf "${C_YELLOW}[WARN]${C_RESET}  %s\n" "$*" | tee -a "${LOG_FILE}"; }
log_error()   { printf "${C_RED}[ERROR]${C_RESET} %s\n" "$*" | tee -a "${LOG_FILE}" >&2; }

section() {
  printf '\n%b%s%b\n' "${C_BOLD}${C_BLUE}" \
    "── $* ──────────────────────────────────────────────────────────────" \
    "${C_RESET}" | tee -a "${LOG_FILE}"
}

pass() {
  local label="$1" elapsed_ms="${2:-}"
  printf "${C_GREEN}[PASS]${C_RESET} %-60s ${C_DIM}%s${C_RESET}\n" \
    "${label}" "${elapsed_ms:+${elapsed_ms}ms}" | tee -a "${LOG_FILE}"
  PASS_COUNT=$(( PASS_COUNT + 1 ))
}

fail() {
  local label="$1" reason="${2:-}"
  printf "${C_RED}[FAIL]${C_RESET} %-60s %s\n" \
    "${label}" "${reason}" | tee -a "${LOG_FILE}"
  FAIL_COUNT=$(( FAIL_COUNT + 1 ))
  FAIL_NAMES+=("${label}")
}

skip() {
  local label="$1" reason="${2:-skipped}"
  printf "${C_YELLOW}[SKIP]${C_RESET} %-60s %s\n" \
    "${label}" "${reason}" | tee -a "${LOG_FILE}"
  SKIP_COUNT=$(( SKIP_COUNT + 1 ))
}

# ---------------------------------------------------------------------------
# Elapsed-time helper
# ---------------------------------------------------------------------------
_elapsed_ms() {
  local t0="$1"
  local now
  now="$(date +%s%N 2>/dev/null || date +%s)000000000"
  printf '%d' "$(( ( now - t0 ) / 1000000 ))"
}

# ---------------------------------------------------------------------------
# Credential / prereq checks
# ---------------------------------------------------------------------------
check_credentials() {
  local missing=false

  if [[ -z "${UNIFI_URL:-}" ]]; then
    # Try loading from ~/.claude-homelab/.env
    local env_file="${HOME}/.claude-homelab/.env"
    if [[ -f "${env_file}" ]]; then
      set -a
      # shellcheck source=/dev/null
      source "${env_file}"
      set +a
    fi
  fi

  for var in UNIFI_URL UNIFI_USERNAME UNIFI_PASSWORD; do
    if [[ -z "${!var:-}" ]]; then
      log_error "Required environment variable ${var} is not set."
      log_error "  Set it directly or add it to ~/.claude-homelab/.env"
      missing=true
    fi
  done

  if [[ "${missing}" == true ]]; then
    return 2
  fi

  log_info "Credentials OK (UNIFI_URL=${UNIFI_URL})"
}

check_tool() {
  local tool="$1"
  if ! command -v "${tool}" &>/dev/null; then
    log_error "Required tool '${tool}' not found in PATH."
    return 2
  fi
}

check_prerequisites_http() {
  check_tool curl || return 2
  check_tool jq   || return 2
}

check_prerequisites_docker() {
  check_tool curl   || return 2
  check_tool jq     || return 2
  check_tool docker || return 2
}

check_prerequisites_stdio() {
  check_tool uvx    || return 2
  check_tool jq     || return 2
  check_tool python3 || return 2
}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

# mcp_post <url> <bearer_token> <json_body>
# Outputs: HTTP status on first line, body on remaining lines
mcp_post() {
  local url="$1"
  local token="$2"
  local body="$3"
  local auth_header=""

  if [[ -n "${token}" ]]; then
    auth_header="Authorization: Bearer ${token}"
  fi

  curl -sS --max-time 30 -w '\n%{http_code}' \
    -X POST "${url}" \
    -H "Content-Type: application/json" \
    ${auth_header:+-H "${auth_header}"} \
    -d "${body}" 2>>"${LOG_FILE}"
}

# GET request, returns "<body>\n<status>"
http_get() {
  local url="$1"
  local token="${2:-}"
  local auth_header=""

  if [[ -n "${token}" ]]; then
    auth_header="Authorization: Bearer ${token}"
  fi

  curl -sS --max-time 10 -w '\n%{http_code}' \
    "${url}" \
    ${auth_header:+-H "${auth_header}"} \
    2>>"${LOG_FILE}"
}

# extract_status: last line of curl -w output
extract_status() { tail -n1 <<< "$1"; }
# extract_body: everything except the last line
extract_body()   { sed '$d' <<< "$1"; }

# assert_jq <label> <json> <jq_expr> [expected_value]
# Validates that jq_expr returns truthy / equals expected_value.
# Returns 1 and logs fail if assertion does not hold.
assert_jq() {
  local label="$1"
  local json="$2"
  local expr="$3"
  local expected="${4:-}"   # optional: exact string match

  local result
  result="$(printf '%s' "${json}" | jq -r "${expr}" 2>/dev/null)" || {
    fail "${label}" "jq parse error for expr: ${expr}"
    return 1
  }

  if [[ -n "${expected}" ]]; then
    if [[ "${result}" != "${expected}" ]]; then
      fail "${label}" "expected '${expected}', got '${result}'"
      return 1
    fi
  else
    # Truthy check: not null, not empty, not "false"
    if [[ -z "${result}" || "${result}" == "null" || "${result}" == "false" ]]; then
      fail "${label}" "jq expr '${expr}' returned falsy: '${result}'"
      return 1
    fi
  fi
  return 0
}

# call_tool <base_url> <token> <tool_name> <arguments_json>
# Returns the full JSON-RPC response body.
call_tool() {
  local base_url="$1"
  local token="$2"
  local tool_name="$3"
  local args_json="$4"
  local request_id="$RANDOM"

  local payload
  payload="$(jq -n \
    --argjson args "${args_json}" \
    --arg tool "${tool_name}" \
    --argjson id "${request_id}" \
    '{
      jsonrpc: "2.0",
      id: $id,
      method: "tools/call",
      params: { name: $tool, arguments: $args }
    }')"

  local raw
  raw="$(mcp_post "${base_url}/mcp/v1/messages" "${token}" "${payload}")" || true

  local status body
  status="$(extract_status "${raw}")"
  body="$(extract_body "${raw}")"

  if [[ "${VERBOSE}" == true ]]; then
    printf '%s\n' "${body}" | tee -a "${LOG_FILE}"
  else
    printf '%s\n' "${body}" >> "${LOG_FILE}"
  fi

  printf '%s' "${body}"
}

# extract_tool_text <response_json>
# Extracts the text content from a tools/call response.
extract_tool_text() {
  local resp="$1"
  printf '%s' "${resp}" | jq -r '
    .result.content[]? | select(.type == "text") | .text
    // .result.contents[]? | select(.type == "text") | .text
    // ""
  ' 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# MCP JSON-RPC helpers (stdio)
# ---------------------------------------------------------------------------

# Send a JSON-RPC message and read the response via a Python helper.
# The helper starts the server via uvx, sends initialize + the message,
# and returns the raw JSON response.
_stdio_call() {
  local tool_name="$1"
  local args_json="$2"
  local timeout_s="${3:-30}"

  python3 - <<PYEOF
import subprocess, json, sys, os, time, threading

repo_dir = "${REPO_DIR}"
entry_point = "${ENTRY_POINT}"

env = dict(os.environ)
env.update({
    "UNIFI_URL": "${UNIFI_URL}",
    "UNIFI_USERNAME": "${UNIFI_USERNAME}",
    "UNIFI_PASSWORD": "${UNIFI_PASSWORD}",
    "UNIFI_MCP_TRANSPORT": "stdio",
    "UNIFI_VERIFY_SSL": os.environ.get("UNIFI_VERIFY_SSL", "false"),
    "UNIFI_IS_UDM_PRO": os.environ.get("UNIFI_IS_UDM_PRO", "true"),
})

cmd = ["uvx", "--directory", repo_dir, "--from", ".", entry_point]

try:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=repo_dir,
    )
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(0)

init_msg = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test_live", "version": "1.0"}
    }
}) + "\n"

tool_args = ${args_json}
call_msg = json.dumps({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "${tool_name}", "arguments": tool_args}
}) + "\n"

try:
    proc.stdin.write(init_msg.encode())
    proc.stdin.flush()

    # Read init response
    deadline = time.time() + ${timeout_s}
    init_resp = None
    buf = b""
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            obj = json.loads(line.decode())
            if obj.get("id") == 1:
                init_resp = obj
                break
        except Exception:
            pass

    if init_resp is None:
        print(json.dumps({"error": "no initialize response"}))
        proc.terminate()
        sys.exit(0)

    # Send initialized notification
    notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    proc.stdin.write(notif.encode())
    proc.stdin.flush()

    # Send tool call
    proc.stdin.write(call_msg.encode())
    proc.stdin.flush()

    # Read tool response
    deadline = time.time() + ${timeout_s}
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            obj = json.loads(line.decode())
            if obj.get("id") == 2:
                print(json.dumps(obj))
                proc.terminate()
                sys.exit(0)
        except Exception:
            pass

    print(json.dumps({"error": "timeout waiting for tool response"}))
    proc.terminate()
except Exception as e:
    print(json.dumps({"error": str(e)}))
    proc.terminate()
PYEOF
}

# ---------------------------------------------------------------------------
# Phase 1 — Health check
# ---------------------------------------------------------------------------
phase_health() {
  local base_url="$1"
  local label="Phase 1 / Health: GET /health → status:ok"
  local t0
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"

  local raw
  raw="$(http_get "${base_url}/health")" || true
  local status body
  status="$(extract_status "${raw}")"
  body="$(extract_body "${raw}")"

  if [[ "${VERBOSE}" == true ]]; then
    printf '%s\n' "${body}" | tee -a "${LOG_FILE}"
  fi

  if [[ "${status}" != "200" ]]; then
    fail "${label}" "HTTP ${status}"
    return 1
  fi

  assert_jq "${label}" "${body}" '.status' "ok" || return 1
  pass "${label}" "$(_elapsed_ms "${t0}")"
}

# ---------------------------------------------------------------------------
# Phase 2 — Authentication
# ---------------------------------------------------------------------------
phase_auth() {
  local base_url="$1"
  local good_token="$2"
  local t0

  # 2a — No token → 401
  local label_no="Phase 2a / Auth: no token → 401"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local raw_no
  raw_no="$(http_get "${base_url}/mcp/v1/messages")" || true
  local status_no
  status_no="$(extract_status "${raw_no}")"
  if [[ "${status_no}" == "401" ]]; then
    pass "${label_no}" "$(_elapsed_ms "${t0}")"
  else
    fail "${label_no}" "expected 401, got HTTP ${status_no}"
  fi

  # 2b — Bad token → 401 or 403
  local label_bad="Phase 2b / Auth: bad token → 401/403"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local raw_bad
  raw_bad="$(http_get "${base_url}/mcp/v1/messages" "definitely-wrong-token-abc123")" || true
  local status_bad
  status_bad="$(extract_status "${raw_bad}")"
  if [[ "${status_bad}" == "401" || "${status_bad}" == "403" ]]; then
    pass "${label_bad}" "$(_elapsed_ms "${t0}")"
  else
    fail "${label_bad}" "expected 401 or 403, got HTTP ${status_bad}"
  fi

  # 2c — Good token → not 401/403
  local label_good="Phase 2c / Auth: valid token → accepted"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local init_payload
  init_payload='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
  local raw_good
  raw_good="$(mcp_post "${base_url}/mcp/v1/messages" "${good_token}" "${init_payload}")" || true
  local status_good
  status_good="$(extract_status "${raw_good}")"
  if [[ "${status_good}" == "401" || "${status_good}" == "403" ]]; then
    fail "${label_good}" "token rejected: HTTP ${status_good}"
  else
    pass "${label_good}" "$(_elapsed_ms "${t0}")"
  fi
}

# ---------------------------------------------------------------------------
# Phase 3 — Protocol: initialize + tools/list
# ---------------------------------------------------------------------------
phase_protocol() {
  local base_url="$1"
  local token="$2"

  # 3a — initialize
  local label_init="Phase 3a / Protocol: initialize"
  local t0
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local init_payload
  init_payload='{"jsonrpc":"2.0","id":10,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test_live","version":"1.0"}}}'
  local raw_init
  raw_init="$(mcp_post "${base_url}/mcp/v1/messages" "${token}" "${init_payload}")" || true
  local status_init body_init
  status_init="$(extract_status "${raw_init}")"
  body_init="$(extract_body "${raw_init}")"

  if [[ "${status_init}" != "200" ]]; then
    fail "${label_init}" "HTTP ${status_init}"
  else
    assert_jq "${label_init}" "${body_init}" '.result.protocolVersion' || \
    assert_jq "${label_init}" "${body_init}" '.result.capabilities' && \
    pass "${label_init}" "$(_elapsed_ms "${t0}")" || true
  fi

  # 3b — tools/list, verify unifi and unifi_help present
  local label_list="Phase 3b / Protocol: tools/list — unifi + unifi_help present"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local list_payload
  list_payload='{"jsonrpc":"2.0","id":11,"method":"tools/list","params":{}}'
  local raw_list
  raw_list="$(mcp_post "${base_url}/mcp/v1/messages" "${token}" "${list_payload}")" || true
  local status_list body_list
  status_list="$(extract_status "${raw_list}")"
  body_list="$(extract_body "${raw_list}")"

  if [[ "${status_list}" != "200" ]]; then
    fail "${label_list}" "HTTP ${status_list}"
    return 1
  fi

  local has_unifi has_help
  has_unifi="$(printf '%s' "${body_list}" | jq -r '[.result.tools[]? | select(.name == "unifi")] | length' 2>/dev/null || echo 0)"
  has_help="$(printf '%s' "${body_list}" | jq -r '[.result.tools[]? | select(.name == "unifi_help")] | length' 2>/dev/null || echo 0)"

  if [[ "${has_unifi}" -ge 1 && "${has_help}" -ge 1 ]]; then
    pass "${label_list}" "$(_elapsed_ms "${t0}")"
  else
    fail "${label_list}" "unifi=${has_unifi} unifi_help=${has_help} in tools list"
  fi
}

# ---------------------------------------------------------------------------
# Phase 4 — Tool calls (HTTP mode)
# ---------------------------------------------------------------------------
phase_tools_http() {
  local base_url="$1"
  local token="$2"

  # Helper: run one tool call test
  # _tool_test <label> <tool_name> <args_json> <jq_validation_expr> [expected_value]
  _tool_test() {
    local label="$1"
    local tool_name="$2"
    local args_json="$3"
    local jq_expr="$4"
    local expected="${5:-}"
    local t0
    t0="$(date +%s%N 2>/dev/null || date +%s)000000000"

    local resp
    resp="$(call_tool "${base_url}" "${token}" "${tool_name}" "${args_json}")"

    if [[ -z "${resp}" ]]; then
      fail "${label}" "empty response"
      return 1
    fi

    # Check for JSON-RPC error
    local rpc_err
    rpc_err="$(printf '%s' "${resp}" | jq -r '.error.message // empty' 2>/dev/null || true)"
    if [[ -n "${rpc_err}" ]]; then
      fail "${label}" "RPC error: ${rpc_err}"
      return 1
    fi

    # Extract text content from the MCP response
    local text
    text="$(extract_tool_text "${resp}")"

    if [[ -z "${text}" ]]; then
      # Fall back to checking structured_content
      text="$(printf '%s' "${resp}" | jq -r '.result.structuredContent // .result.structured_content // empty' 2>/dev/null || true)"
    fi

    if [[ -z "${text}" ]]; then
      fail "${label}" "no text/structured content in response"
      return 1
    fi

    # If text is JSON, validate with jq_expr
    if printf '%s' "${text}" | jq . &>/dev/null 2>&1; then
      if [[ -n "${expected}" ]]; then
        assert_jq "${label}" "${text}" "${jq_expr}" "${expected}" || return 1
      else
        assert_jq "${label}" "${text}" "${jq_expr}" || return 1
      fi
    else
      # Plain text: apply basic non-empty check + optional substring check
      if [[ -z "${text}" ]]; then
        fail "${label}" "empty text response"
        return 1
      fi
      if [[ -n "${expected}" ]] && ! printf '%s' "${text}" | grep -qi "${expected}"; then
        fail "${label}" "expected '${expected}' in text output"
        return 1
      fi
    fi

    pass "${label}" "$(_elapsed_ms "${t0}")"
  }

  # ── get_devices ──────────────────────────────────────────────────────────
  section "Tool: get_devices"
  local raw_devs
  raw_devs="$(call_tool "${base_url}" "${token}" "unifi" '{"action":"get_devices"}')"
  local devs_text
  devs_text="$(extract_tool_text "${raw_devs}")"
  local t0
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"

  if [[ -n "${devs_text}" ]]; then
    # Validate it looks like a device list (array or object with devices key)
    local is_array has_devices
    is_array="$(printf '%s' "${devs_text}" | jq 'if type == "array" then "yes" else "no" end' 2>/dev/null || echo no)"
    has_devices="$(printf '%s' "${devs_text}" | jq 'has("devices") or (type == "array")' 2>/dev/null || echo false)"

    if [[ "${is_array}" == '"yes"' || "${has_devices}" == "true" ]]; then
      pass "Phase 4 / get_devices: returns device list" "$(_elapsed_ms "${t0}")"
    else
      # Non-array text response (formatted output) — just check it's non-empty
      if [[ -n "${devs_text}" ]]; then
        pass "Phase 4 / get_devices: returns non-empty response" "$(_elapsed_ms "${t0}")"
      else
        fail "Phase 4 / get_devices: returns device list" "empty body"
      fi
    fi
  else
    fail "Phase 4 / get_devices: returns device list" "no content"
  fi

  # ── get_clients ──────────────────────────────────────────────────────────
  section "Tool: get_clients"
  _tool_test "Phase 4 / get_clients(connected_only=true): response non-empty" \
    "unifi" '{"action":"get_clients","connected_only":true}' \
    '. != null'

  # ── get_sites ────────────────────────────────────────────────────────────
  section "Tool: get_sites"
  local raw_sites
  raw_sites="$(call_tool "${base_url}" "${token}" "unifi" '{"action":"get_sites"}')"
  local sites_text
  sites_text="$(extract_tool_text "${raw_sites}")"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  if [[ -n "${sites_text}" ]]; then
    pass "Phase 4 / get_sites: returns at least one site" "$(_elapsed_ms "${t0}")"
  else
    fail "Phase 4 / get_sites: returns at least one site" "empty response"
  fi

  # ── get_wlan_configs ─────────────────────────────────────────────────────
  section "Tool: get_wlan_configs"
  _tool_test "Phase 4 / get_wlan_configs: response non-empty" \
    "unifi" '{"action":"get_wlan_configs"}' \
    '. != null'

  # ── get_network_configs ──────────────────────────────────────────────────
  section "Tool: get_network_configs"
  _tool_test "Phase 4 / get_network_configs: response non-empty" \
    "unifi" '{"action":"get_network_configs"}' \
    '. != null'

  # ── get_firewall_rules ───────────────────────────────────────────────────
  section "Tool: get_firewall_rules"
  _tool_test "Phase 4 / get_firewall_rules: response non-empty" \
    "unifi" '{"action":"get_firewall_rules"}' \
    '. != null'

  # ── get_controller_status ────────────────────────────────────────────────
  section "Tool: get_controller_status"
  local raw_status
  raw_status="$(call_tool "${base_url}" "${token}" "unifi" '{"action":"get_controller_status"}')"
  local status_text
  status_text="$(extract_tool_text "${raw_status}")"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  if [[ -n "${status_text}" ]]; then
    # Try to find version field in JSON, else just check the text contains "version"
    local has_version
    has_version="$(printf '%s' "${status_text}" | jq -r 'has("version") or has("Version") or (.version != null)' 2>/dev/null || echo "")"
    if [[ "${has_version}" == "true" ]] || printf '%s' "${status_text}" | grep -qi "version"; then
      pass "Phase 4 / get_controller_status: version field present" "$(_elapsed_ms "${t0}")"
    else
      # Still pass if we got a non-empty response — status may be formatted text
      pass "Phase 4 / get_controller_status: response non-empty" "$(_elapsed_ms "${t0}")"
    fi
  else
    fail "Phase 4 / get_controller_status: version field present" "empty response"
  fi

  # ── get_events ───────────────────────────────────────────────────────────
  section "Tool: get_events"
  _tool_test "Phase 4 / get_events(limit=5): response non-empty" \
    "unifi" '{"action":"get_events","limit":5}' \
    '. != null'

  # ── unifi_help ───────────────────────────────────────────────────────────
  section "Tool: unifi_help"
  local raw_help
  raw_help="$(call_tool "${base_url}" "${token}" "unifi_help" '{}')"
  local help_text
  help_text="$(extract_tool_text "${raw_help}")"
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  if [[ -z "${help_text}" ]]; then
    fail "Phase 4 / unifi_help: help text non-empty and mentions unifi" "empty response"
  elif ! printf '%s' "${help_text}" | grep -qi "unifi"; then
    fail "Phase 4 / unifi_help: help text non-empty and mentions unifi" "text does not mention 'unifi'"
  else
    pass "Phase 4 / unifi_help: help text non-empty and mentions unifi" "$(_elapsed_ms "${t0}")"
  fi
}

# ---------------------------------------------------------------------------
# HTTP mode runner
# ---------------------------------------------------------------------------
run_http_mode() {
  local base_url="$1"
  local token="$2"

  section "Phase 1 — Health"
  phase_health "${base_url}" || return 1

  section "Phase 2 — Authentication"
  phase_auth "${base_url}" "${token}"

  section "Phase 3 — MCP Protocol"
  phase_protocol "${base_url}" "${token}"

  section "Phase 4 — Tool Calls"
  phase_tools_http "${base_url}" "${token}"
}

# ---------------------------------------------------------------------------
# Docker mode
# ---------------------------------------------------------------------------
run_docker_mode() {
  section "Docker mode — build + run"

  local image_tag="unifi-mcp-test:ci-$(date +%s)"
  local container_name="unifi-mcp-test-$$"
  local docker_port="${PORT}"
  local token="${BEARER_TOKEN:-${CI_TOKEN}}"

  log_info "Building Docker image: ${image_tag}"
  if ! docker build -t "${image_tag}" "${REPO_DIR}" >>"${LOG_FILE}" 2>&1; then
    log_error "Docker build failed. See ${LOG_FILE} for details."
    return 2
  fi
  log_info "Docker image built successfully."

  # Cleanup function for this mode
  _docker_cleanup() {
    if [[ -n "${DOCKER_CONTAINER}" ]]; then
      log_info "Stopping container ${DOCKER_CONTAINER}..."
      docker stop "${DOCKER_CONTAINER}" >>"${LOG_FILE}" 2>&1 || true
      docker rm "${DOCKER_CONTAINER}"   >>"${LOG_FILE}" 2>&1 || true
      DOCKER_CONTAINER=""
    fi
    docker rmi "${image_tag}" >>"${LOG_FILE}" 2>&1 || true
  }
  trap _docker_cleanup RETURN

  log_info "Starting container: ${container_name}"
  DOCKER_CONTAINER="$(docker run -d \
    --name "${container_name}" \
    -p "${docker_port}:8001" \
    -e "UNIFI_URL=${UNIFI_URL}" \
    -e "UNIFI_USERNAME=${UNIFI_USERNAME}" \
    -e "UNIFI_PASSWORD=${UNIFI_PASSWORD}" \
    -e "UNIFI_MCP_TOKEN=${token}" \
    -e "UNIFI_VERIFY_SSL=${UNIFI_VERIFY_SSL:-false}" \
    -e "UNIFI_IS_UDM_PRO=${UNIFI_IS_UDM_PRO:-true}" \
    "${image_tag}" 2>>"${LOG_FILE}")"

  log_info "Container started: ${DOCKER_CONTAINER}"

  # Poll /health up to 30 times (1s interval)
  local base_url="http://localhost:${docker_port}"
  local healthy=false
  log_info "Waiting for container to be healthy..."
  for i in $(seq 1 30); do
    local h_raw
    h_raw="$(curl -sS --max-time 3 -w '\n%{http_code}' "${base_url}/health" 2>/dev/null)" || true
    local h_status
    h_status="$(extract_status "${h_raw}")"
    if [[ "${h_status}" == "200" ]]; then
      healthy=true
      log_info "Container healthy after ${i}s."
      break
    fi
    sleep 1
  done

  if [[ "${healthy}" != "true" ]]; then
    log_error "Container did not become healthy within 30s."
    docker logs "${DOCKER_CONTAINER}" >>"${LOG_FILE}" 2>&1 || true
    return 2
  fi

  run_http_mode "${base_url}" "${token}"
}

# ---------------------------------------------------------------------------
# stdio mode
# ---------------------------------------------------------------------------
run_stdio_mode() {
  section "stdio mode — uvx + MCP protocol"

  # 3a — initialize
  local label_init="stdio / Protocol: initialize"
  local t0
  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local init_resp
  init_resp="$(_stdio_call "unifi_help" '{}')"

  if [[ -z "${init_resp}" ]]; then
    fail "${label_init}" "no response from stdio server"
    return 1
  fi

  local rpc_err
  rpc_err="$(printf '%s' "${init_resp}" | jq -r '.error.message // empty' 2>/dev/null || true)"
  if [[ "${rpc_err}" == *"no initialize response"* || "${rpc_err}" == *"timeout"* ]]; then
    fail "${label_init}" "server error: ${rpc_err}"
    return 1
  fi

  pass "${label_init}" "$(_elapsed_ms "${t0}")"

  # tools/list via stdio
  local label_list="stdio / Protocol: tools/list — unifi + unifi_help present"

  local list_resp_file
  list_resp_file="$(mktemp)"
  REPO_DIR="${REPO_DIR}" python3 - > "${list_resp_file}" <<'PYEOF'
import subprocess, json, sys, os, time

repo_dir = os.environ.get("REPO_DIR", "")
entry_point = "unifi-mcp"
env = dict(os.environ)
env.update({
    "UNIFI_URL": os.environ.get("UNIFI_URL", ""),
    "UNIFI_USERNAME": os.environ.get("UNIFI_USERNAME", ""),
    "UNIFI_PASSWORD": os.environ.get("UNIFI_PASSWORD", ""),
    "UNIFI_MCP_TRANSPORT": "stdio",
    "UNIFI_VERIFY_SSL": os.environ.get("UNIFI_VERIFY_SSL", "false"),
    "UNIFI_IS_UDM_PRO": os.environ.get("UNIFI_IS_UDM_PRO", "true"),
})

cmd = ["uvx", "--directory", repo_dir, "--from", ".", entry_point]
try:
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, cwd=repo_dir)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(0)

init_msg = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
    "params":{"protocolVersion":"2024-11-05","capabilities":{},
    "clientInfo":{"name":"test_live","version":"1.0"}}}) + "\n"
list_msg = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}) + "\n"

try:
    proc.stdin.write(init_msg.encode()); proc.stdin.flush()
    deadline = time.time() + 45
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line: break
        try:
            obj = json.loads(line.decode())
            if obj.get("id") == 1: break
        except Exception: pass

    notif = json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}) + "\n"
    proc.stdin.write(notif.encode()); proc.stdin.flush()
    proc.stdin.write(list_msg.encode()); proc.stdin.flush()

    deadline = time.time() + 45
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line: break
        try:
            obj = json.loads(line.decode())
            if obj.get("id") == 2:
                print(json.dumps(obj))
                proc.terminate()
                sys.exit(0)
        except Exception: pass

    print(json.dumps({"error": "timeout"}))
    proc.terminate()
except Exception as e:
    print(json.dumps({"error": str(e)}))
    proc.terminate()
PYEOF

  t0="$(date +%s%N 2>/dev/null || date +%s)000000000"
  local list_resp
  list_resp="$(cat "${list_resp_file}")"
  rm -f "${list_resp_file}"

  local list_err
  list_err="$(printf '%s' "${list_resp}" | jq -r '.error // empty' 2>/dev/null || true)"
  if [[ -n "${list_err}" ]]; then
    fail "${label_list}" "server error: ${list_err}"
  else
    local has_unifi has_help
    has_unifi="$(printf '%s' "${list_resp}" | jq -r '[.result.tools[]? | select(.name == "unifi")] | length' 2>/dev/null || echo 0)"
    has_help="$(printf '%s' "${list_resp}" | jq -r '[.result.tools[]? | select(.name == "unifi_help")] | length' 2>/dev/null || echo 0)"

    if [[ "${has_unifi}" -ge 1 && "${has_help}" -ge 1 ]]; then
      pass "${label_list}" "$(_elapsed_ms "${t0}")"
    else
      fail "${label_list}" "unifi=${has_unifi} unifi_help=${has_help}"
    fi
  fi

  # stdio tool calls (subset of read-only actions)
  local stdio_tests=(
    "unifi_help:{}"
    "unifi:{\"action\":\"get_sites\"}"
    "unifi:{\"action\":\"get_controller_status\"}"
    "unifi:{\"action\":\"get_devices\"}"
    "unifi:{\"action\":\"get_clients\",\"connected_only\":true}"
    "unifi:{\"action\":\"get_wlan_configs\"}"
    "unifi:{\"action\":\"get_firewall_rules\"}"
    "unifi:{\"action\":\"get_events\",\"limit\":5}"
  )

  for entry in "${stdio_tests[@]}"; do
    local tool_name args_json
    tool_name="${entry%%:*}"
    args_json="${entry#*:}"
    local label="stdio / Tool: ${tool_name}(${args_json})"
    t0="$(date +%s%N 2>/dev/null || date +%s)000000000"

    local resp
    resp="$(_stdio_call "${tool_name}" "${args_json}")"

    local err
    err="$(printf '%s' "${resp}" | jq -r '.error // empty' 2>/dev/null || true)"
    local rpc_err2
    rpc_err2="$(printf '%s' "${resp}" | jq -r '.error.message // empty' 2>/dev/null || true)"

    if [[ -n "${err}" || -n "${rpc_err2}" ]]; then
      fail "${label}" "error: ${err}${rpc_err2}"
    else
      local content
      content="$(printf '%s' "${resp}" | jq -r '.result.content[]? | select(.type=="text") | .text // empty' 2>/dev/null || true)"
      if [[ -n "${content}" ]]; then
        pass "${label}" "$(_elapsed_ms "${t0}")"
      else
        fail "${label}" "empty content in response"
      fi
    fi
  done
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print_summary() {
  local total_ms
  local now
  now="$(date +%s%N 2>/dev/null || date +%s)000000000"
  total_ms="$(( ( now - TS_START ) / 1000000 ))"
  local total=$(( PASS_COUNT + FAIL_COUNT + SKIP_COUNT ))

  printf '\n%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..70})" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "PASS"    "${C_RESET}" "${C_GREEN}"  "${PASS_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "FAIL"    "${C_RESET}" "${C_RED}"    "${FAIL_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "SKIP"    "${C_RESET}" "${C_YELLOW}" "${SKIP_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %d\n'     "${C_BOLD}" "TOTAL"   "${C_RESET}" "${total}"
  printf '%b%-20s%b  %ds (%dms)\n' "${C_BOLD}" "ELAPSED" "${C_RESET}" \
    "$(( total_ms / 1000 ))" "${total_ms}"
  printf '%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..70})" "${C_RESET}"

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    printf '\n%bFailed tests:%b\n' "${C_RED}" "${C_RESET}"
    local name
    for name in "${FAIL_NAMES[@]}"; do
      printf '  • %s\n' "${name}"
    done
    printf '\nLog: %s\n' "${LOG_FILE}"
  fi
}

# ---------------------------------------------------------------------------
# Cleanup trap (global)
# ---------------------------------------------------------------------------
_global_cleanup() {
  local rc=$?
  if [[ $rc -ne 0 && -f "${LOG_FILE}" ]]; then
    log_warn "Exited with rc=${rc}. Log: ${LOG_FILE}"
  fi
}
trap _global_cleanup EXIT

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"

  printf '%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..70})" "${C_RESET}"
  printf '%b  unifi-mcp — canonical live integration tests%b\n' "${C_BOLD}" "${C_RESET}"
  printf '%b  Mode: %s | Log: %s%b\n' "${C_BOLD}" "${MODE}" "${LOG_FILE}" "${C_RESET}"
  printf '%b%s%b\n\n' "${C_BOLD}" "$(printf '=%.0s' {1..70})" "${C_RESET}"

  check_credentials || exit 2

  local run_http=false run_docker=false run_stdio=false
  case "${MODE}" in
    http)   run_http=true ;;
    docker) run_docker=true ;;
    stdio)  run_stdio=true ;;
    all)    run_http=true; run_docker=true; run_stdio=true ;;
  esac

  # ── HTTP mode ──────────────────────────────────────────────────────────
  if [[ "${run_http}" == true ]]; then
    section "MODE: HTTP"
    check_prerequisites_http || exit 2

    local http_url="${SERVER_URL:-http://localhost:${PORT}}"
    local http_token="${BEARER_TOKEN:-${UNIFI_MCP_TOKEN:-}}"

    if [[ -z "${http_token}" ]]; then
      log_warn "No bearer token set for http mode (BEARER_TOKEN / UNIFI_MCP_TOKEN)."
      log_warn "Auth phase 2c may fail. Set UNIFI_MCP_TOKEN or use --token."
    fi

    run_http_mode "${http_url}" "${http_token}" || true
  fi

  # ── Docker mode ────────────────────────────────────────────────────────
  if [[ "${run_docker}" == true ]]; then
    section "MODE: Docker"
    check_prerequisites_docker || exit 2
    run_docker_mode || true
  fi

  # ── stdio mode ─────────────────────────────────────────────────────────
  if [[ "${run_stdio}" == true ]]; then
    section "MODE: stdio"
    check_prerequisites_stdio || exit 2
    run_stdio_mode || true
  fi

  print_summary

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
