# Output Style Definitions

Custom formatting for agent and tool responses.

## Current State

unifi-mcp does not define custom output styles. Tool responses use the built-in `ToolResult` format with text content and structured content.

## Response Formatting

Tool responses follow conventions in [MCPUI.md](../mcp/MCPUI.md):

- Human-readable text layer: compact, token-efficient summaries
- Structured content layer: JSON for programmatic access
- Consistent error format: `Error: {message}`
- Data formatting: bytes to KB/MB/GB, timestamps to ISO 8601

These formatting patterns are implemented in `unifi_mcp/formatters.py` rather than as plugin output styles.

## See Also

- [MCPUI](../mcp/MCPUI.md) — Response format conventions
- [PATTERNS](../mcp/PATTERNS.md) — Code patterns
