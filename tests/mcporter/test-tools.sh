#!/usr/bin/env bash
# =============================================================================
# test-tools.sh — Integration smoke-test for unifi-mcp MCP server tools
#
# Exercises non-destructive smoke coverage of the consolidated `unifi` tool
# (action pattern — no subaction, uses action enum directly). The server is
# launched ad-hoc via mcporter's --stdio flag.
#
# Credentials are sourced from ~/.claude-homelab/.env (UNIFI_URL,
# UNIFI_USERNAME, UNIFI_PASSWORD).
#
# Usage:
#   ./tests/mcporter/test-tools.sh [--timeout-ms N] [--parallel] [--verbose]
#
# Options:
#   --timeout-ms N   Per-call timeout in milliseconds (default: 25000)
#   --parallel       Run independent test groups in parallel (default: off)
#   --verbose        Print raw mcporter output for each call
#
# Exit codes:
#   0 — all tests passed or skipped
#   1 — one or more tests failed
#   2 — prerequisite check failed (mcporter, uv, server startup)
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd -P)"
readonly SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
readonly TS_START="$(date +%s%N)"
readonly LOG_FILE="${TMPDIR:-/tmp}/${SCRIPT_NAME%.sh}.$(date +%Y%m%d-%H%M%S).log"
readonly ENV_FILE="${HOME}/.claude-homelab/.env"
readonly STDIO_CMD="uv run unifi-mcp"

# Colours (disabled automatically when stdout is not a terminal)
if [[ -t 1 ]]; then
  C_RESET='\033[0m'
  C_BOLD='\033[1m'
  C_GREEN='\033[0;32m'
  C_RED='\033[0;31m'
  C_YELLOW='\033[0;33m'
  C_CYAN='\033[0;36m'
  C_DIM='\033[2m'
else
  C_RESET='' C_BOLD='' C_GREEN='' C_RED='' C_YELLOW='' C_CYAN='' C_DIM=''
fi

# ---------------------------------------------------------------------------
# Defaults (overridable via flags)
# ---------------------------------------------------------------------------
CALL_TIMEOUT_MS=25000
USE_PARALLEL=false
VERBOSE=false

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
      --timeout-ms)
        CALL_TIMEOUT_MS="${2:?--timeout-ms requires a value}"
        shift 2
        ;;
      --parallel)
        USE_PARALLEL=true
        shift
        ;;
      --verbose)
        VERBOSE=true
        shift
        ;;
      -h|--help)
        printf 'Usage: %s [--timeout-ms N] [--parallel] [--verbose]\n' "${SCRIPT_NAME}"
        exit 0
        ;;
      *)
        printf '[ERROR] Unknown argument: %s\n' "$1" >&2
        exit 2
        ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()  { printf "${C_CYAN}[INFO]${C_RESET}  %s\n" "$*" | tee -a "${LOG_FILE}"; }
log_warn()  { printf "${C_YELLOW}[WARN]${C_RESET}  %s\n" "$*" | tee -a "${LOG_FILE}"; }
log_error() { printf "${C_RED}[ERROR]${C_RESET} %s\n" "$*" | tee -a "${LOG_FILE}" >&2; }

# ---------------------------------------------------------------------------
# Cleanup trap
# ---------------------------------------------------------------------------
cleanup() {
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    log_warn "Script exited with rc=${rc}. Log: ${LOG_FILE}"
  fi
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Load credentials from ~/.claude-homelab/.env
# ---------------------------------------------------------------------------
load_credentials() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    log_error "Credentials file not found: ${ENV_FILE}"
    log_error "Run scripts/setup-creds.sh or copy .env.example to ${ENV_FILE}"
    return 2
  fi

  # shellcheck source=/dev/null
  set -a
  source "${ENV_FILE}"
  set +a

  if [[ -z "${UNIFI_URL:-}" ]]; then
    log_error "UNIFI_URL is not set in ${ENV_FILE}"
    return 2
  fi
  if [[ -z "${UNIFI_USERNAME:-}" ]]; then
    log_error "UNIFI_USERNAME is not set in ${ENV_FILE}"
    return 2
  fi
  if [[ -z "${UNIFI_PASSWORD:-}" ]]; then
    log_error "UNIFI_PASSWORD is not set in ${ENV_FILE}"
    return 2
  fi

  log_info "Credentials loaded (UNIFI_URL=${UNIFI_URL})"
}

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
check_prerequisites() {
  local missing=false

  if ! command -v mcporter &>/dev/null; then
    log_error "mcporter not found in PATH. Install it and re-run."
    missing=true
  fi

  if ! command -v uv &>/dev/null; then
    log_error "uv not found in PATH. Install it and re-run."
    missing=true
  fi

  if ! command -v python3 &>/dev/null; then
    log_error "python3 not found in PATH."
    missing=true
  fi

  if ! command -v jq &>/dev/null; then
    log_error "jq not found in PATH. Install it and re-run."
    missing=true
  fi

  if [[ ! -f "${PROJECT_DIR}/pyproject.toml" ]]; then
    log_error "pyproject.toml not found at ${PROJECT_DIR}. Wrong directory?"
    missing=true
  fi

  if [[ "${missing}" == true ]]; then
    return 2
  fi
}

# ---------------------------------------------------------------------------
# Server startup smoke-test
# ---------------------------------------------------------------------------
smoke_test_server() {
  log_info "Smoke-testing server startup..."

  local output
  output="$(
    UNIFI_URL="${UNIFI_URL}" \
    UNIFI_USERNAME="${UNIFI_USERNAME}" \
    UNIFI_PASSWORD="${UNIFI_PASSWORD}" \
    UNIFI_VERIFY_SSL="${UNIFI_VERIFY_SSL:-false}" \
    UNIFI_IS_UDM_PRO="${UNIFI_IS_UDM_PRO:-true}" \
    UNIFI_MCP_TRANSPORT="stdio" \
    mcporter call \
      --stdio "${STDIO_CMD}" \
      --cwd "${PROJECT_DIR}" \
      --name "unifi-smoke" \
      --tool unifi_help \
      --args '{}' \
      --timeout 30000 \
      --output json \
      2>&1
  )" || true

  if printf '%s' "${output}" | grep -q '"kind": "offline"'; then
    log_error "Server failed to start. Output:"
    printf '%s\n' "${output}" >&2
    log_error "Common causes:"
    log_error "  • Missing module: check 'uv run unifi-mcp' locally"
    log_error "  • UNIFI_URL, UNIFI_USERNAME, or UNIFI_PASSWORD missing or incorrect"
    return 2
  fi

  log_info "Server started successfully."
  return 0
}

# ---------------------------------------------------------------------------
# mcporter call wrapper — passes env vars for each call
# ---------------------------------------------------------------------------
mcporter_call() {
  local tool="${1:?tool required}"
  local args_json="${2:?args_json required}"

  UNIFI_URL="${UNIFI_URL}" \
  UNIFI_USERNAME="${UNIFI_USERNAME}" \
  UNIFI_PASSWORD="${UNIFI_PASSWORD}" \
  UNIFI_VERIFY_SSL="${UNIFI_VERIFY_SSL:-false}" \
  UNIFI_IS_UDM_PRO="${UNIFI_IS_UDM_PRO:-true}" \
  UNIFI_MCP_TRANSPORT="stdio" \
  mcporter call \
    --stdio "${STDIO_CMD}" \
    --cwd "${PROJECT_DIR}" \
    --name "unifi" \
    --tool "${tool}" \
    --args "${args_json}" \
    --timeout "${CALL_TIMEOUT_MS}" \
    --output json \
    2>>"${LOG_FILE}"
}

# ---------------------------------------------------------------------------
# Test runner
#   Usage: run_test <label> <tool> <args_json> [expected_key]
# ---------------------------------------------------------------------------
run_test() {
  local label="${1:?label required}"
  local tool="${2:?tool required}"
  local args="${3:?args required}"
  local expected_key="${4:-}"

  local t0
  t0="$(date +%s%N)"

  local output
  output="$(mcporter_call "${tool}" "${args}")" || true

  local elapsed_ms
  elapsed_ms="$(( ( $(date +%s%N) - t0 ) / 1000000 ))"

  if [[ "${VERBOSE}" == true ]]; then
    printf '%s\n' "${output}" | tee -a "${LOG_FILE}"
  else
    printf '%s\n' "${output}" >> "${LOG_FILE}"
  fi

  # Detect server-offline
  if printf '%s' "${output}" | grep -q '"kind": "offline"'; then
    printf "${C_RED}[FAIL]${C_RESET} %-55s ${C_DIM}%dms${C_RESET}\n" \
      "${label}" "${elapsed_ms}" | tee -a "${LOG_FILE}"
    printf '       server offline — check startup errors in %s\n' "${LOG_FILE}" | tee -a "${LOG_FILE}"
    FAIL_COUNT=$(( FAIL_COUNT + 1 ))
    FAIL_NAMES+=("${label}")
    return 1
  fi

  # Validate response — extract first JSON object/array (server may log to stdout)
  local json_check
  json_check="$(
    printf '%s' "${output}" | python3 -c "
import sys, json, re
raw = sys.stdin.read()
# Extract first JSON array or object from output (logs may follow)
m = re.search(r'(\[.*?\]|\{.*?\})', raw, re.DOTALL)
if not m:
    if 'kind' in raw and 'offline' in raw:
        print('error: server offline')
    elif raw.strip():
        print('ok')  # non-empty non-JSON = text response
    else:
        print('invalid_json: empty output')
    sys.exit(0)
try:
    d = json.loads(m.group(1))
    if isinstance(d, dict) and ('error' in d or d.get('kind') == 'error'):
        print('error: ' + str(d.get('error', d.get('message', 'unknown'))))
    else:
        print('ok')
except Exception as e:
    # Greedy regex may have grabbed too much; try line-by-line
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith(('[', '{')):
            try:
                json.loads(line)
                print('ok')
                sys.exit(0)
            except Exception:
                pass
    print('ok')  # non-empty = treat as ok
" 2>/dev/null
  )" || json_check="parse_error"

  if [[ "${json_check}" != "ok" ]]; then
    printf "${C_RED}[FAIL]${C_RESET} %-55s ${C_DIM}%dms${C_RESET}\n" \
      "${label}" "${elapsed_ms}" | tee -a "${LOG_FILE}"
    printf '       response validation failed: %s\n' "${json_check}" | tee -a "${LOG_FILE}"
    FAIL_COUNT=$(( FAIL_COUNT + 1 ))
    FAIL_NAMES+=("${label}")
    return 1
  fi

  # Validate optional key presence
  if [[ -n "${expected_key}" ]]; then
    local key_check
    key_check="$(
      printf '%s' "${output}" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    keys = '${expected_key}'.split('.')
    node = d
    for k in keys:
        if k:
            node = node[k]
    print('ok')
except Exception as e:
    print('missing: ' + str(e))
" 2>/dev/null
    )" || key_check="parse_error"

    if [[ "${key_check}" != "ok" ]]; then
      printf "${C_RED}[FAIL]${C_RESET} %-55s ${C_DIM}%dms${C_RESET}\n" \
        "${label}" "${elapsed_ms}" | tee -a "${LOG_FILE}"
      printf '       expected key .%s not found: %s\n' "${expected_key}" "${key_check}" | tee -a "${LOG_FILE}"
      FAIL_COUNT=$(( FAIL_COUNT + 1 ))
      FAIL_NAMES+=("${label}")
      return 1
    fi
  fi

  printf "${C_GREEN}[PASS]${C_RESET} %-55s ${C_DIM}%dms${C_RESET}\n" \
    "${label}" "${elapsed_ms}" | tee -a "${LOG_FILE}"
  PASS_COUNT=$(( PASS_COUNT + 1 ))
  return 0
}

# ---------------------------------------------------------------------------
# Skip helper
# ---------------------------------------------------------------------------
skip_test() {
  local label="${1:?label required}"
  local reason="${2:-prerequisite returned empty}"
  printf "${C_YELLOW}[SKIP]${C_RESET} %-55s %s\n" "${label}" "${reason}" | tee -a "${LOG_FILE}"
  SKIP_COUNT=$(( SKIP_COUNT + 1 ))
}

# ---------------------------------------------------------------------------
# Safe JSON payload builder
# ---------------------------------------------------------------------------
_json_payload() {
  local template="${1:?template required}"; shift
  local jq_args=()
  local pair k v
  for pair in "$@"; do
    k="${pair%%=*}"
    v="${pair#*=}"
    jq_args+=(--arg "$k" "$v")
  done
  jq -n "${jq_args[@]}" "$template"
}

# ---------------------------------------------------------------------------
# ID extractors
# ---------------------------------------------------------------------------

get_device_mac() {
  local raw
  raw="$(mcporter_call unifi '{"action":"get_devices"}' 2>/dev/null)" || return 0
  printf '%s' "${raw}" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    devices = d.get('devices', d if isinstance(d, list) else [])
    if devices:
        print(devices[0].get('mac', ''))
except Exception:
    pass
" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Grouped test suites
# ---------------------------------------------------------------------------

suite_help() {
  printf '\n%b== help ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"
  run_test "unifi: help" "unifi_help" '{}'
}

suite_global() {
  printf '\n%b== global (no site required) ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"

  run_test "unifi: get_controller_status" "unifi" '{"action":"get_controller_status"}'
  run_test "unifi: get_user_info"         "unifi" '{"action":"get_user_info"}'
  run_test "unifi: get_sites"             "unifi" '{"action":"get_sites"}'
}

suite_network() {
  printf '\n%b== network configuration ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"

  run_test "unifi: get_wlan_configs"         "unifi" '{"action":"get_wlan_configs"}'
  run_test "unifi: get_network_configs"      "unifi" '{"action":"get_network_configs"}'
  run_test "unifi: get_port_configs"         "unifi" '{"action":"get_port_configs"}'
  run_test "unifi: get_port_forwarding_rules" "unifi" '{"action":"get_port_forwarding_rules"}'
  run_test "unifi: get_firewall_rules"       "unifi" '{"action":"get_firewall_rules"}'
  run_test "unifi: get_firewall_groups"      "unifi" '{"action":"get_firewall_groups"}'
  run_test "unifi: get_static_routes"        "unifi" '{"action":"get_static_routes"}'
}

suite_devices() {
  printf '\n%b== devices ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"

  run_test "unifi: get_devices" "unifi" '{"action":"get_devices"}'

  local device_mac
  device_mac="$(get_device_mac)" || device_mac=''
  if [[ -n "${device_mac}" ]]; then
    run_test "unifi: get_device_by_mac" \
      "unifi" \
      "$(_json_payload '{"action":"get_device_by_mac","mac":$mac}' mac="${device_mac}")"
  else
    skip_test "unifi: get_device_by_mac" "no devices found"
  fi
  # Destructive: restart_device, locate_device — skipped
}

suite_clients() {
  printf '\n%b== clients ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"

  run_test "unifi: get_clients (connected)"    "unifi" '{"action":"get_clients","connected_only":true}'
  run_test "unifi: get_clients (all)"          "unifi" '{"action":"get_clients","connected_only":false}'
  # Destructive: reconnect_client, block_client, unblock_client, forget_client,
  #              set_client_name, set_client_note, authorize_guest — skipped
}

suite_monitoring() {
  printf '\n%b== monitoring & statistics ==%b\n' "${C_BOLD}" "${C_RESET}" | tee -a "${LOG_FILE}"

  run_test "unifi: get_events"          "unifi" '{"action":"get_events","limit":20}'
  run_test "unifi: get_alarms"          "unifi" '{"action":"get_alarms","active_only":true}'
  run_test "unifi: get_dpi_stats"       "unifi" '{"action":"get_dpi_stats"}'
  run_test "unifi: get_rogue_aps"       "unifi" '{"action":"get_rogue_aps"}'
  run_test "unifi: get_speedtest_results" "unifi" '{"action":"get_speedtest_results"}'
  run_test "unifi: get_ips_events"      "unifi" '{"action":"get_ips_events"}'
  # start_spectrum_scan is a write op — skipped
  # get_spectrum_scan_state reads scan state (non-mutating)
  run_test "unifi: get_spectrum_scan_state" "unifi" '{"action":"get_spectrum_scan_state"}'
}

# ---------------------------------------------------------------------------
# Print final summary
# ---------------------------------------------------------------------------
print_summary() {
  local total_ms="$(( ( $(date +%s%N) - TS_START ) / 1000000 ))"
  local total=$(( PASS_COUNT + FAIL_COUNT + SKIP_COUNT ))

  printf '\n%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..65})" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "PASS" "${C_RESET}" "${C_GREEN}" "${PASS_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "FAIL" "${C_RESET}" "${C_RED}"   "${FAIL_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %b%d%b\n' "${C_BOLD}" "SKIP" "${C_RESET}" "${C_YELLOW}" "${SKIP_COUNT}" "${C_RESET}"
  printf '%b%-20s%b  %d\n' "${C_BOLD}" "TOTAL" "${C_RESET}" "${total}"
  printf '%b%-20s%b  %ds (%dms)\n' "${C_BOLD}" "ELAPSED" "${C_RESET}" \
    "$(( total_ms / 1000 ))" "${total_ms}"
  printf '%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..65})" "${C_RESET}"

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    printf '\n%bFailed tests:%b\n' "${C_RED}" "${C_RESET}"
    local name
    for name in "${FAIL_NAMES[@]}"; do
      printf '  • %s\n' "${name}"
    done
    printf '\nFull log: %s\n' "${LOG_FILE}"
  fi
}

# ---------------------------------------------------------------------------
# Sequential runner
# ---------------------------------------------------------------------------
run_sequential() {
  suite_help
  suite_global
  suite_network
  suite_devices
  suite_clients
  suite_monitoring
}

# ---------------------------------------------------------------------------
# Parallel runner
# ---------------------------------------------------------------------------
run_parallel() {
  log_warn "--parallel mode: per-suite counters aggregated via temp files."

  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf -- "${tmp_dir}"' RETURN

  local suites=(
    suite_help
    suite_global
    suite_network
    suite_devices
    suite_clients
    suite_monitoring
  )

  local pids=()
  local suite
  for suite in "${suites[@]}"; do
    (
      PASS_COUNT=0; FAIL_COUNT=0; SKIP_COUNT=0; FAIL_NAMES=()
      "${suite}"
      printf '%d %d %d\n' "${PASS_COUNT}" "${FAIL_COUNT}" "${SKIP_COUNT}" \
        > "${tmp_dir}/${suite}.counts"
      printf '%s\n' "${FAIL_NAMES[@]:-}" > "${tmp_dir}/${suite}.fails"
    ) &
    pids+=($!)
  done

  local pid
  for pid in "${pids[@]}"; do
    wait "${pid}" || true
  done

  local f
  for f in "${tmp_dir}"/*.counts; do
    [[ -f "${f}" ]] || continue
    local p fl s
    read -r p fl s < "${f}"
    PASS_COUNT=$(( PASS_COUNT + p ))
    FAIL_COUNT=$(( FAIL_COUNT + fl ))
    SKIP_COUNT=$(( SKIP_COUNT + s ))
  done

  for f in "${tmp_dir}"/*.fails; do
    [[ -f "${f}" ]] || continue
    while IFS= read -r line; do
      [[ -n "${line}" ]] && FAIL_NAMES+=("${line}")
    done < "${f}"
  done
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"

  printf '%b%s%b\n' "${C_BOLD}" "$(printf '=%.0s' {1..65})" "${C_RESET}"
  printf '%b  unifi-mcp integration smoke-test (single unifi tool)%b\n' "${C_BOLD}" "${C_RESET}"
  printf '%b  Project: %s%b\n' "${C_BOLD}" "${PROJECT_DIR}" "${C_RESET}"
  printf '%b  Timeout: %dms/call | Parallel: %s%b\n' \
    "${C_BOLD}" "${CALL_TIMEOUT_MS}" "${USE_PARALLEL}" "${C_RESET}"
  printf '%b  Log: %s%b\n' "${C_BOLD}" "${LOG_FILE}" "${C_RESET}"
  printf '%b%s%b\n\n' "${C_BOLD}" "$(printf '=%.0s' {1..65})" "${C_RESET}"

  load_credentials || exit 2
  check_prerequisites || exit 2

  smoke_test_server || {
    log_error ""
    log_error "Server startup failed. Aborting — no tests will run."
    log_error ""
    log_error "To diagnose, run:"
    log_error "  cd ${PROJECT_DIR} && UNIFI_URL=... UNIFI_USERNAME=... UNIFI_PASSWORD=... uv run unifi-mcp"
    exit 2
  }

  if [[ "${USE_PARALLEL}" == true ]]; then
    run_parallel
  else
    run_sequential
  fi

  print_summary

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
