# AI Review Content from PR #1

**Extracted from PR:** https://github.com/jmagar/unifi-mcp/pull/1
**Original items found:** 40
**Items filtered out:** 1
**Final items kept:** 39

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -        self.client = UnifiControllerClient(self.unifi_config)
> -        await self.client.connect()
> +        self.client = UnifiControllerClient(self.unifi_config)
> +        try:
> +            await self.client.connect()
> +        except Exception as e:
> +            logger.error(f"Failed to connect to UniFi controller: {e}")
> +            # Optionally: raise to abort startup
> +            raise
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -            # First get the client to find its ID
> -            clients = await client.get_clients(site_name)
> -            client_id = None
> -
> -            if isinstance(clients, list):
> -                for client_data in clients:
> -                    if client_data.get("mac", "").lower().replace("-", ":").replace(".", ":") == normalized_mac:
> -                        client_id = client_data.get("_id")
> -                        break
> +            # Resolve user id from controller users, not active sessions
> +            users = await client._make_request("GET", "/list/user", site_name=site_name)
> +            client_id = None
> +            if isinstance(users, list):
> +                for u in users:
> +                    if (u.get("mac", "").lower().replace("-", ":").replace(".", ":")) == normalized_mac:
> +                        client_id = u.get("_id") or u.get("user_id")
> +                        break
> +            elif isinstance(users, dict) and "error" in users:
> +                return ToolResult(
> +                    content=[TextContent(type="text", text=f"Error: {users.get('error','unknown error')}")],
> +                    structured_content={"error": users.get("error","unknown error"), "raw": users}
> +                )
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -            # First get the client to find its ID
> -            clients = await client.get_clients(site_name)
> -            client_id = None
> -
> -            if isinstance(clients, list):
> -                for client_data in clients:
> -                    if client_data.get("mac", "").lower().replace("-", ":").replace(".", ":") == normalized_mac:
> -                        client_id = client_data.get("_id")
> -                        break
> +            users = await client._make_request("GET", "/list/user", site_name=site_name)
> +            client_id = None
> +            if isinstance(users, list):
> +                for u in users:
> +                    if (u.get("mac", "").lower().replace("-", ":").replace(".", ":")) == normalized_mac:
> +                        client_id = u.get("_id") or u.get("user_id")
> +                        break
> +            elif isinstance(users, dict) and "error" in users:
> +                return ToolResult(
> +                    content=[TextContent(type="text", text=f"Error: {users.get('error','unknown error')}")],
> +                    structured_content={"error": users.get("error","unknown error"), "raw": users}
> +                )
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -                    "ssid": wlan.get("x_iapp_key", wlan.get("name", "Unknown")),
> +                    # SSID is typically under 'ssid' (fallback to profile 'name')
> +                    "ssid": wlan.get("ssid", wlan.get("name", "Unknown SSID")),
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
>                  formatted_rule = {
> @@
> -                    "direction": rule.get("rule_index", "unknown"),
> +                    "ruleset": rule.get("ruleset", "unknown"),
> +                    "index": rule.get("rule_index", None),
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -            for event in events[-limit:]:  # Get most recent events
> +            events_sorted = sorted(
> +                events, key=lambda e: e.get("time", e.get("timestamp", 0)), reverse=True
> +            )[:limit]
> +            for event in events_sorted:
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> -                formatted_stat["summary"] = {
> +                tx_raw = formatted_stat.get("tx_bytes_raw", 0) or 0
> +                rx_raw = formatted_stat.get("rx_bytes_raw", 0) or 0
> +                formatted_stat["summary"] = {
>                      "application": stat.get("app", stat.get("cat", "Unknown")),
> -                    "total_bytes": formatted_stat.get("tx_bytes", "0 B") + " / " + formatted_stat.get("rx_bytes", "0 B"),
> +                    "tx": formatted_stat.get("tx_bytes", "0 B"),
> +                    "rx": formatted_stat.get("rx_bytes", "0 B"),
> +                    "total_bytes_raw": tx_raw + rx_raw,
>                      "last_seen": format_timestamp(stat.get("time", 0))
>                  }
>

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
>          data = {
>              "cmd": "authorize-guest",
>              "mac": normalized_mac,
>              "minutes": minutes
>          }
> +        if minutes <= 0:
> +            return ToolResult(
> +                content=[TextContent(type="text", text="Error: minutes must be > 0")],
> +                structured_content=[{"error": "invalid_minutes"}]
> +            )
> +        for k, v in (("up", up_bandwidth), ("down", down_bandwidth), ("bytes_mb", quota)):
> +            if v is not None and v < 0:
> +                return ToolResult(
> +                    content=[TextContent(type="text", text=f"Error: {k} must be non-negative")],
> +                    structured_content=[{"error": f"invalid_{k}"}]
> +                )
>

---

- [ ] [PYTHON BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> def _normalize_mac(mac: str) -> str:
>     return mac.strip().lower().replace("-", ":").replace(".", ":")
>

---

- [ ] [PYTHON BLOCK - coderabbitai[bot] - unifi_mcp/server.py:74-77]
> def _normalize_mac(mac: str) -> str:
>     return mac.strip().lower().replace("-", ":").replace(".", ":")
>

---

- [ ] [COPILOT REVIEW - Copilot]
# Always format bytes for consistency
        txf = format_bytes(tx)
        rxf = format_bytes(rx)

---

- [ ] [AI PROMPT - docs/token-efficient-formatting.md:17]
docs/token-efficient-formatting.md around lines 7 to 17: the section incorrectly
refers to "Docker MCP" and docker_* commands which are not part of this UniFi
MCP project; update the terminology and examples to refer to UniFi MCP
(clients/devices/networks), replace docker_* command names and examples with
UniFi-equivalent commands/objects, and ensure any sample ToolResult/response
snippets reflect UniFi data shapes and CLI usage; alternatively, if this content
belongs to another repo, move the file there and replace with UniFi-specific
content or a pointer to the correct location.

---

- [ ] [AI PROMPT - docs/token-efficient-formatting.md:371]
`
In docs/token-efficient-formatting.md around lines 291 to 371, several
markdownlint failures (missing blank lines around fenced code blocks,
unspecified fence languages, and trailing spaces) break CI and reduce
readability; fix by ensuring a blank line before and after each fenced block,
add an appropriate language identifier after each opening

---

- [ ] [AI PROMPT - docs/token-efficient-formatting.md:371]
text or

---

- [ ] [AI PROMPT - docs/token-efficient-formatting.md:371]
diff where applicable), remove trailing whitespace on all affected
lines, and re-run markdownlint/CI; you can apply these edits manually or run an
automated fixer targeting MD031, MD040 and MD009 to update the file and confirm
the linter passes.

---

- [ ] [AI PROMPT - docs/tools.md:14]
In docs/tools.md lines 1-14: the file contains MDX/JSX (exported React component
and inline HTML) which will not render on GitHub and triggers markdownlint;
either rename the file to docs/tools.mdx so the site/build treats it as MDX, or
remove/replace all JSX with Markdown-safe content (e.g., remove the
export/component and replace the version badge with a plain Markdown badge or an
inline code block and standard headings/paragraphs); ensure to update any
imports/links that reference docs/tools.md if you rename the file.

---

- [ ] [AI PROMPT - docs/tools.md:127]
In docs/tools.md around lines 27 to 127, the file was replaced with a generic
FastMCP how-to but the PR requires a UniFi-specific reference documenting all 29
UniFi MCP tools; replace the current generic content with a UniFi MCP tools
reference (or restore the previous TOOLS.md) that lists each of the 29 tools
with name, description, parameters (types/defaults), example usage, and any
tags/annotations; generate the content by scanning the current UniFi MCP code to
extract tool metadata and signatures, include a short example for each tool and
note any unsupported parameter patterns (e.g., *args/**kwargs), and if helpful
open an issue to track missing examples or gaps and scaffold the document
structure so maintainers can review and fill in remaining details.

---

- [ ] [AI PROMPT - docs/tools.md:551]
`
In docs/tools.md around lines 509 to 551, several fenced code blocks are missing
language identifiers (e.g., the Python and JSON blocks shown), which breaks
syntax highlighting and linter rules; add appropriate language tags to every
fence (

---

- [ ] [AI PROMPT - docs/tools.md:551]
json for JSON blocks, etc.), run your
markdown linter or Prettier MDX plugin to auto-fix remaining untagged fences
across the file (and all noted line ranges), verify tags are correct for each
snippet, and commit the updated markdown.

---

- [ ] [AI PROMPT - pyproject.toml:33]
In pyproject.toml around lines 31 to 33, add uvicorn as a runtime dependency by
adding "uvicorn>=0.30.0" to the [project].dependencies list so that imports and
uvicorn.Server usage in unifi_mcp/server.py resolve at runtime; update the
dependencies entry accordingly and run a build/lock step to ensure the new
dependency is recorded.

---

- [ ] [AI PROMPT - unifi_mcp/formatters.py:616]
In unifi_mcp/formatters.py around lines 611 to 616, the event timestamp is
currently appended raw — set ts = e.get("timestamp") or e.get("time") or "" and
pass that value through the existing format_timestamp(...) function before
formatting the line so listings show human-readable times; ensure you handle
empty/None values returned from format_timestamp (fall back to empty string) and
import or reference format_timestamp from the same module if not already
available.

---

- [ ] [AI PROMPT - unifi_mcp/formatters.py:633]
In unifi_mcp/formatters.py around lines 627 to 633, the alarm timestamp is taken
raw (ts = a.get("timestamp", "")) and should be passed through format_timestamp
for consistent display; replace that assignment with ts =
format_timestamp(a.get("timestamp", "")) (or ts = "" if no timestamp) so the
subsequent line uses the formatted timestamp, ensuring format_timestamp is
available in the module.

---

- [ ] [AI PROMPT - unifi_mcp/formatters.py:696]
In unifi_mcp/formatters.py around lines 691-696 the speed-test output uses the
raw ts = r.get("timestamp", "") which is not humanized; replace ts with the same
humanizing/formatting function used earlier in this file (e.g., format_timestamp
or humanize_timestamp) before building the line so timestamps are readable (fall
back to the original ts or an empty string if the helper returns None).

---

- [ ] [AI PROMPT - unifi_mcp/formatters.py:714]
In unifi_mcp/formatters.py around lines 708 to 714, the timestamp for IPS events
is being used raw; convert the event "timestamp" into a human-readable string
(e.g., ISO8601 or "%Y-%m-%d %H:%M:%S %Z") before appending to lines. Parse
numeric epoch or ISO strings with datetime (handle both int/float and string),
format to a clear local/UTC representation, wrap in try/except and fall back to
the original value on parse failure, then use that formatted ts in the f-string.

---

- [ ] [AI PROMPT - unifi_mcp/server.py:68]
In unifi_mcp/server.py around lines 41 to 68, the current logic treats any
non-empty FASTMCP_SERVER_AUTH as Google, doesn't validate required Google env
vars, can produce an empty scopes list, and doesn't expose whether auth actually
enabled; change the check to only enable Google when FASTMCP_SERVER_AUTH ==
"google", validate that FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID,
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET, and
FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL are present and non-empty and log a clear
error and abort auth setup if any are missing, build scopes by splitting
FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES, filtering out empty strings and
defaulting to ["openid","email","profile"] when none provided, construct
GoogleProvider only after validation succeeds, set self._auth_enabled = True on
success and False on any fallback path (including exceptions), and always ensure
self.mcp is created (with auth only when _auth_enabled is True) while using
clear log messages for each decision.

---

- [ ] [AI PROMPT - unifi_mcp/server.py:88]
In unifi_mcp/server.py around lines 85 to 88, the code currently checks the
environment variable directly to gate registration of auth tools; change to an
instance flag set in __init__ by reading auth_provider =
os.getenv("FASTMCP_SERVER_AUTH") then immediately assigning self._auth_enabled =
bool(auth_provider), and replace the env-var check at lines 85–88 with if
self._auth_enabled: self._register_auth_tools() so registration is driven by the
configured provider state rather than re-reading the environment.

---

- [ ] [DIFF BLOCK - coderabbitai[bot] - unifi_mcp/server.py:142]
@self.mcp.tool
         async def get_user_info() -> dict:
@@
             try:
                 # Import here to avoid issues if not using authentication
                 from fastmcp.server.dependencies import get_access_token
-                
-                token = get_access_token()
+                token = get_access_token()
+                # If get_access_token becomes async in future versions:
+                # token = await get_access_token()
                 # The GoogleProvider stores user data in token claims
-                user_info = {
+                from datetime import datetime, timezone
+                def _to_iso(ts):
+                    try:
+                        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
+                    except Exception:
+                        return ts
+                user_info = {
                     "google_id": token.claims.get("sub"),
                     "email": token.claims.get("email"),
                     "name": token.claims.get("name"),
                     "picture": token.claims.get("picture"),
                     "locale": token.claims.get("locale"),
                     "verified_email": token.claims.get("email_verified"),
-                    "token_issued_at": token.claims.get("iat"),
-                    "token_expires_at": token.claims.get("exp")
+                    "token_issued_at": _to_iso(token.claims.get("iat")),
+                    "token_expires_at": _to_iso(token.claims.get("exp")),
+                    "authenticated": True,
                 }
                 
-                logger.info(f"User authenticated: {user_info.get('email', 'unknown')}")
+                logger.debug("User authenticated.")
                 return user_info

---

- [ ] [AI PROMPT - unifi_mcp/tools/client_tools.py:47]
In unifi_mcp/tools/client_tools.py around lines 37 to 47, the two error branches
return different structured_content shapes and lose the raw controller payload;
make both branches return a consistent dict shape like {"error": <message>,
"raw": <original_response>} so callers can always expect the same keys and you
preserve the original controller payload for debugging; update the first branch
to include the original clients dict under "raw" instead of returning it
directly, and update the second branch to include the original non-list response
(e.g., clients) under "raw" while keeping the "error" message.

---

- [ ] [AI PROMPT - unifi_mcp/tools/client_tools.py:112]
In unifi_mcp/tools/client_tools.py around lines 98 to 112, the code returns a
reconnect success without verifying the API return code; mirror the device tools
pattern by checking result.get("meta", {}).get("rc") (or similar RC field)
before reporting success. If meta.rc indicates failure (non-zero or missing),
return a ToolResult with an error TextContent and the full
structured_content=result; otherwise construct the success resp and ToolResult
as now. Ensure you use result.get("meta", {}).get("rc") == 0 (or explicit
comparison used in device tools) to gate the success path and include the
original result in structured_content for both success and error responses.

---

- [ ] [SUGGESTION - coderabbitai[bot] - unifi_mcp/tools/client_tools.py:157]
if isinstance(result, dict):
                rc = result.get("meta", {}).get("rc")
                if rc and rc != "ok":
                    msg = result.get("meta", {}).get("msg") or result.get("error") or "Controller returned failure"
                    return ToolResult(
                        content=[TextContent(type="text", text=f"Error: {msg}")],
                        structured_content={"error": msg, "raw": result}
                    )

            resp = {
                "success": True,
                "message": f"Client {normalized_mac} has been blocked from network access",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Blocked client: {normalized_mac}")],
                structured_content=resp
            )

---

- [ ] [AI PROMPT - unifi_mcp/tools/client_tools.py:202]
In unifi_mcp/tools/client_tools.py around lines 187 to 202, ensure the error and
success responses use the same result-code/rc guard and consistently reference
normalized_mac in user-facing messages and structured payloads: when result is
an error, return structured_content with "success": False (or equivalent rc) and
include normalized_mac in the TextContent and structured response; when success,
continue to set "success": True and use normalized_mac (not the original mac
variable) in both the human-readable text and the resp["mac"] field so both
branches follow the same rc semantics and use the normalized MAC.

---

- [ ] [SUGGESTION - coderabbitai[bot] - unifi_mcp/tools/client_tools.py:247]
if isinstance(result, dict):
                rc = result.get("meta", {}).get("rc")
                if rc and rc != "ok":
                    msg = (
                        result.get("meta", {}).get("msg")
                        or result.get("error")
                        or "Controller returned failure"
                    )
                    return ToolResult(
                        content=[TextContent(type="text", text=f"Error: {msg}")],
                        structured_content={"error": msg, "raw": result}
                    )

            resp = {
                "success": True,
                "message": f"Client {normalized_mac} historical data has been removed",
                "mac": normalized_mac,
                "details": result
            }
            return ToolResult(
                content=[TextContent(type="text", text=f"Forgot client data: {normalized_mac}")],
                structured_content=resp
            )

---

- [ ] [AI PROMPT - unifi_mcp/tools/client_tools.py:314]
In unifi_mcp/tools/client_tools.py around lines 296 to 314, the success path
assumes any non-error dict result means the update succeeded and uses the
original mac for display; instead, check result.get("meta", {}).get("rc") and
treat non-zero or missing rc as an error returning a ToolResult with the error
message, and use normalized_mac (not the un-normalized mac variable) when
building resp and the human-friendly nice string so displayed MACs are
consistent; keep existing structured_content but ensure error branches return
early when meta.rc indicates failure.

---

- [ ] [AI PROMPT - unifi_mcp/tools/client_tools.py:381]
In unifi_mcp/tools/client_tools.py around lines 363 to 381, the code currently
only checks for "error" in result and uses the original mac in messages; update
the guard to also detect non-zero return codes (e.g., if isinstance(result,
dict) and (result.get("error") or result.get("rc"))) to treat failures
uniformly, and replace occurrences of mac in user-facing message and nice string
with normalized_mac (and in the error ToolResult text) so all responses
consistently show the normalized MAC; keep structured_content=result (or resp on
success) and ensure success is only returned when rc is missing or zero.

---

- [ ] [AI PROMPT - unifi_mcp/tools/device_tools.py:46]
In unifi_mcp/tools/device_tools.py around lines 37-46 and 93-103, the review
notes that structured_content is sometimes a list and sometimes a dict on error
paths; standardize it to always be a dict with explicit keys like "error"
(string) and "raw" (original response) so downstream code can rely on a
consistent shape. Replace the current returns that set
structured_content=[devices] or structured_content=[{"error": "..."}] with
structured_content={"error": "<message>", "raw": devices_or_response}, and keep
content as the human-readable TextContent message; ensure both error branches
follow the same dict shape and update any surrounding code/comments accordingly.

---

- [ ] [AI PROMPT - unifi_mcp/tools/device_tools.py:166]
In unifi_mcp/tools/device_tools.py around lines 151 to 166, the current logic
treats any response without an "error" key as success; instead check
result.get("meta", {}).get("rc") == "ok" before claiming success. If meta.rc !=
"ok" or meta is missing, return a ToolResult containing a TextContent with the
controller's message(s) and the full structured result; if rc == "ok" return
success as before but include the meta and any controller messages in the
structured_content and compose the success text using those details. Ensure you
read controller messages from result.get("meta", {}).get("msg") or similar
fields and surface them in both the human text and structured_content.

---

- [ ] [AI PROMPT - unifi_mcp/tools/device_tools.py:204]
In unifi_mcp/tools/device_tools.py around lines 190 to 204, the locate_device
success branch currently treats any non-dict-or-error result as success and can
return false positives; apply the same meta.rc check used in the restart fix:
inspect result.get("meta", {}).get("rc") and if it's not 0 (or meta missing),
return a ToolResult with an error TextContent and the full structured result,
otherwise build the resp success dict and return the successful ToolResult as
before. Ensure you preserve existing message/fields and only treat rc==0 as
success.

---

- [ ] [SUGGESTION - coderabbitai[bot] - unifi_mcp/tools/monitoring_tools.py:61]
if isinstance(result, dict) and "error" in result:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: {result.get('error','unknown error')}")],
                    structured_content=[result]
                )
            if not isinstance(result, dict):
                return ToolResult(
                    content=[TextContent(type="text", text=f"Error: Unexpected response format: {type(result).__name__}")],
                    structured_content=[{"error": f"Unexpected response format: {type(result).__name__}"}]
                )

            resp = {
                "status": "online",
                "server_version": result.get("server_version", "Unknown"),
                "up": result.get("up", False),
                "details": result
            }
            up_icon = "✓" if resp.get("up") else "✗"
            text = f"Controller Status\n  Version: {resp['server_version']} | Up: {up_icon}"
            return ToolResult(
                content=[TextContent(type="text", text=text)],
                structured_content=resp
            )

---

- [ ] [AI PROMPT - unifi_mcp/tools/network_tools.py:254]
In unifi_mcp/tools/network_tools.py around lines 240 to 254, the summary header
is ambiguous because "Native" shows a networkconf ID fragment while "Tagged"
shows a count; update the header and label text to make types explicit (e.g.,
change header to "Native(ID)" and "Tagged(#)" or similar), and keep the per-port
values as currently produced but ensure the native column is clearly presented
as an ID fragment and the tagged column as a count; adjust the header string(s)
and any accompanying separator to match the new labels so the columns align.
