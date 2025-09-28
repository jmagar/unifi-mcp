# FastMCP Parameter Type Annotations: The Complete Guide

## Overview

This guide documents the correct patterns for defining parameter type annotations in FastMCP tools to ensure proper type introspection and avoid "unknown" parameter types in MCP client interfaces.

## The Problem

When using FastMCP, parameters can show up as "unknown" type in MCP clients, making it difficult for users and LLMs to understand what types of values are expected. This issue is caused by incorrect type annotation patterns that confuse FastMCP's Pydantic-based type introspection system.

## The Solution: Working Patterns

### ✅ Required Parameters

For required parameters, use this pattern:

```python
from typing import Annotated
from pydantic import Field

@mcp.tool
def example_tool(
    # Required string with validation
    host_id: Annotated[str, Field(description="Host identifier", min_length=1)],
    
    # Required integer with constraints
    port: Annotated[int, Field(description="Port number", ge=1, le=65535)],
    
    # Required literal (enum-like)
    action: Annotated[Literal["start", "stop", "restart"], Field(description="Action to perform")],
    
    # Required boolean
    enabled: Annotated[bool, Field(description="Whether feature is enabled")]
) -> dict:
    pass
```

### ✅ Optional Parameters

For optional parameters, **always include `default=` in the Field AND provide a default value**:

```python
@mcp.tool
def example_tool(
    # Optional string
    ssh_key_path: Annotated[str, Field(default="", description="Path to SSH private key file")] = "",
    
    # Optional integer with constraints
    timeout: Annotated[int, Field(default=30, ge=1, le=300, description="Timeout in seconds")] = 30,
    
    # Optional boolean
    test_connection: Annotated[bool, Field(default=True, description="Test connection")] = True,
    
    # Optional list with default_factory
    tags: Annotated[list[str], Field(default_factory=list, description="List of tags")] = [],
    
    # Optional dict with default_factory
    metadata: Annotated[dict[str, str], Field(default_factory=dict, description="Metadata")] = {},
    
    # Optional enum-like parameter (use str, not Literal for optional)
    log_level: Annotated[str, Field(default="info", description="Log level")] = "info"
) -> dict:
    pass
```

### Key Rules for Optional Parameters

1. **Use `default=` in Field** - Always specify the default value in the Field definition
2. **Provide default value after `=`** - Also provide the default value after the parameter annotation
3. **No `| None` unions** - Avoid union types entirely for FastMCP compatibility
4. **Use `default_factory=` for collections** - For lists/dicts, use `default_factory=list` or `default_factory=dict`
5. **Use `str` instead of `Literal` for optional enums** - Literal types in optional parameters cause issues

## ❌ Patterns That Don't Work

### Union Types Inside Annotated

```python
# ❌ WRONG - Union inside Annotated
ssh_key_path: Annotated[str | None, Field(description="Path to SSH private key")]

# ❌ WRONG - Optional with union inside Annotated
tags: Annotated[list[str] | None, Field(description="Host tags")]
```

### Union Types Outside Annotated

```python
# ❌ WRONG - Union outside Annotated
ssh_key_path: Annotated[str, Field(description="Path to SSH private key")] | None

# ❌ WRONG - This also doesn't work
compose_path: Annotated[str, Field(description="Docker Compose file path")] | None = None
```

### Missing Default in Field

```python
# ❌ WRONG - Missing default= in Field
ssh_key_path: Annotated[str, Field(description="Path to SSH private key")] = ""

# ❌ WRONG - FastMCP needs explicit default in Field
timeout: Annotated[int, Field(ge=1, le=300, description="Timeout")] = 30
```

### Simple Union Types Without Field

```python
# ❌ WRONG - Simple union types show as "unknown"
ssh_key_path: str | None = None
tags: list[str] | None = None
```

## Complete Example

Here's a complete example showing the correct patterns:

```python
from typing import Annotated, Literal
from pydantic import Field
from fastmcp import FastMCP

mcp = FastMCP(name="ExampleServer")

@mcp.tool
async def manage_host(
    # Required parameters
    action: Annotated[Literal["add", "remove", "update"], Field(description="Action to perform")],
    host_id: Annotated[str, Field(description="Host identifier", min_length=1)],
    
    # Optional string parameters
    ssh_key_path: Annotated[str, Field(default="", description="Path to SSH private key file")] = "",
    description: Annotated[str, Field(default="", description="Host description")] = "",
    
    # Optional integer parameters
    ssh_port: Annotated[int, Field(default=22, ge=1, le=65535, description="SSH port number")] = 22,
    timeout: Annotated[int, Field(default=30, ge=1, le=300, description="Connection timeout")] = 30,
    
    # Optional boolean parameters
    test_connection: Annotated[bool, Field(default=True, description="Test connection when adding host")] = True,
    enabled: Annotated[bool, Field(default=True, description="Whether host is enabled")] = True,
    
    # Optional collection parameters
    tags: Annotated[list[str], Field(default_factory=list, description="Host tags")] = [],
    metadata: Annotated[dict[str, str], Field(default_factory=dict, description="Host metadata")] = {},
    
    # Optional enum-like parameters (use str for optional)
    log_level: Annotated[str, Field(default="info", description="Log level (debug, info, warn, error)")] = "info",
    cleanup_type: Annotated[str, Field(default="", description="Type of cleanup to perform")] = "",
    
    # Advanced validation examples
    email: Annotated[str, Field(default="", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Email address")] = "",
    schedule_time: Annotated[str, Field(default="", pattern=r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", description="Time in HH:MM format")] = ""
) -> dict[str, Any]:
    """Manage Docker hosts with comprehensive parameter validation."""
    return {"success": True, "action": action, "host_id": host_id}
```

## Validation Constraints

FastMCP supports all Pydantic validation constraints:

```python
# Numeric constraints
count: Annotated[int, Field(default=0, ge=0, le=100, description="Count (0-100)")] = 0,
ratio: Annotated[float, Field(default=1.0, gt=0, lt=2.0, description="Ratio (0-2)")] = 1.0,
multiple: Annotated[int, Field(default=10, multiple_of=5, description="Must be multiple of 5")] = 10,

# String constraints
name: Annotated[str, Field(default="", min_length=1, max_length=50, description="Name (1-50 chars)")] = "",
pattern_field: Annotated[str, Field(default="", pattern=r"^[A-Z]{2}\d{4}$", description="Pattern: XX0000")] = "",

# Collection constraints
items: Annotated[list[str], Field(default_factory=list, min_length=0, max_length=10, description="0-10 items")] = [],
```

## Troubleshooting "Unknown" Parameter Types

### Step 1: Check the Pattern

Ensure your parameters follow the correct pattern:

```python
# ✅ CORRECT
parameter: Annotated[Type, Field(default=default_value, description="...")] = default_value
```

### Step 2: Avoid Union Types

If a parameter shows as "unknown", check if it uses union types:

```python
# ❌ Remove this
parameter: str | None = None

# ✅ Replace with this  
parameter: Annotated[str, Field(default="", description="...")] = ""
```

### Step 3: Add Explicit Defaults

Ensure both `default=` in Field and `= value` are present:

```python
# ❌ Missing default in Field
parameter: Annotated[str, Field(description="...")] = ""

# ✅ Add explicit default
parameter: Annotated[str, Field(default="", description="...")] = ""
```

### Step 4: Use default_factory for Collections

For lists and dicts, use `default_factory`:

```python
# ✅ Lists
tags: Annotated[list[str], Field(default_factory=list, description="Tags")] = []

# ✅ Dicts  
metadata: Annotated[dict[str, str], Field(default_factory=dict, description="Metadata")] = {}
```

### Step 5: Test MCP Introspection

After making changes:

1. Restart your FastMCP server
2. Reconnect your MCP client
3. Check that parameters show proper types (string, integer, boolean, array, object)
4. If any still show "unknown", verify they follow the patterns above

## Summary

The key to proper FastMCP parameter type annotations:

1. **Required**: `Annotated[Type, Field(description="...")]`
2. **Optional**: `Annotated[Type, Field(default=value, description="...")] = value`
3. **Collections**: Use `default_factory=list` or `default_factory=dict`
4. **No Unions**: Avoid `| None` entirely
5. **Explicit Defaults**: Always specify `default=` in Field for optional parameters
6. **Use `str` for optional enums**: Instead of `Literal` for optional enum-like parameters

Following these patterns ensures all parameters appear with correct types in MCP client interfaces, providing better usability for both human users and LLMs.
