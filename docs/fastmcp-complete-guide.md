# FastMCP Complete Guide: Consolidated Tools & Parameter Annotations

## Overview

This comprehensive guide covers two essential FastMCP patterns:

1. **Consolidated Action-Parameter Pattern** - Architectural approach for grouping related operations
2. **Parameter Type Annotations** - Proper annotation techniques to avoid "unknown" parameter types

Together, these patterns create efficient, maintainable, and user-friendly FastMCP servers.

---

# Part I: Consolidated Action-Parameter Pattern

## What is the Consolidated Action-Parameter Pattern?

The Consolidated Action-Parameter Pattern is an architectural approach for organizing FastMCP tools that groups related operations under a single tool with an `action` parameter, rather than creating separate tools for each operation.

## Benefits

### Context Efficiency
- **Token Reduction**: Our 3 consolidated tools (27 actions) use ~5k tokens vs Playwright's 21 individual tools using ~9.7k tokens
- **2.6x more efficient**: 181 tokens per function vs 464 tokens per function
- **Better scaling**: Adding new actions to existing tools is more efficient than creating new tools

### User Experience
- **Cleaner interface**: 3 logical groups instead of 27 separate tools
- **Easier discovery**: Related operations are grouped together
- **Consistent parameters**: Shared parameters like `host_id` defined once per group
- **Logical organization**: Operations naturally group by domain (hosts, containers, stacks)

### Maintainability
- **Reduced duplication**: Common validation and error handling
- **Centralized routing**: Single dispatch point per domain
- **Consistent patterns**: Uniform approach across all operations

## Implementation Pattern

### 1. Basic Structure

```python
from typing import Annotated, Any
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

# Import enum classes for type-safe actions
from .models.enums import HostAction
from .models.params import DockerHostsParams

class ConsolidatedServer:
    def __init__(self, config):
        self.app = FastMCP(name="ConsolidatedServer")
        
        # Register tools using method registration pattern
        self.app.tool(
            self.domain_manager,
            annotations={
                "title": "Domain Management",
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": True,
            }
        )
    
    async def domain_manager(
        self,
        # Action parameter - accepts string, enum, or None with default
        action: Annotated[
            str | HostAction | None,
            Field(default=None, description="Action to perform (defaults to list if not provided)")
        ] = None,
        
        # Core parameters - conditionally required based on action
        resource_id: Annotated[str, Field(default="", description="Resource identifier")] = "",
        
        # Optional parameters - provide defaults for all actions
        name: Annotated[str, Field(default="", description="Resource name")] = "",
        description: Annotated[str, Field(default="", description="Resource description")] = "",
        tags: Annotated[list[str] | None, Field(default=None, description="Resource tags")] = None,
        
        # Action-specific parameters - only used by certain actions
        force: Annotated[bool, Field(default=False, description="Force the operation")] = False,
        dry_run: Annotated[bool, Field(default=False, description="Perform a dry run")] = False
    ) -> ToolResult | dict[str, Any]:
    """Consolidated resource management tool.
    
    Actions:
    • list: List all resources
      - Required: none
      
    • create: Create a new resource
      - Required: name
      - Optional: description, tags
      
    • update: Update an existing resource
      - Required: resource_id
      - Optional: name, description, tags
      
    • delete: Delete a resource
      - Required: resource_id
      - Optional: force, dry_run
    """
    
    # Parse and validate parameters using parameter model
    try:
        # Convert string action to enum
        if isinstance(action, str):
            action_enum = HostAction(action)
        elif action is None:
            action_enum = HostAction.LIST
        else:
            action_enum = action

        # Use parameter model for validation
        params = DockerHostsParams(
            action=action_enum,
            resource_id=resource_id,
            name=name,
            description=description,
            tags=tags or [],
            force=force,
            dry_run=dry_run
        )
        
        # Use validated enum from parameter model
        action = params.action
    except Exception as e:
        return {
            "success": False,
            "error": f"Parameter validation failed: {str(e)}",
            "action": str(action) if action else "unknown",
        }

    # Delegate to service layer for business logic
    return await self.resource_service.handle_action(
        action, **params.model_dump(exclude={"action"})
    )
```

### 2. Action Parameter Design

#### Use Enum Classes for Type Safety

```python
# ✅ Good - Enum classes for type safety and IDE support
from enum import Enum

class HostAction(Enum):
    LIST = "list"
    ADD = "add"
    EDIT = "edit"
    REMOVE = "remove"
    TEST_CONNECTION = "test_connection"
    DISCOVER = "discover"
    PORTS = "ports"
    IMPORT_SSH = "import_ssh"
    CLEANUP = "cleanup"

# Action parameter accepts string, enum, or None
action: Annotated[
    str | HostAction | None,
    Field(default=None, description="Action to perform (defaults to list if not provided)")
] = None

# ❌ Avoid - Too generic without enum validation
action: Annotated[str, Field(description="Action to perform")]
```

#### Group Related Operations by Domain

```python
# ✅ Good groupings by domain with enum classes
class HostAction(Enum):
    LIST = "list"
    ADD = "add"
    EDIT = "edit" 
    REMOVE = "remove"
    TEST_CONNECTION = "test_connection"
    DISCOVER = "discover"
    PORTS = "ports"
    IMPORT_SSH = "import_ssh"
    CLEANUP = "cleanup"

class ContainerAction(Enum):
    LIST = "list"
    INFO = "info"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    LOGS = "logs"
    REMOVE = "remove"

class ComposeAction(Enum):
    LIST = "list"
    DISCOVER = "discover"
    VIEW = "view"
    DEPLOY = "deploy"
    UP = "up"
    DOWN = "down"
    RESTART = "restart"
    BUILD = "build"
    LOGS = "logs"
    MIGRATE = "migrate"

# ❌ Avoid mixing unrelated domains
mixed_actions = ["list_hosts", "start_container", "deploy_stack"]  # Too broad
```

# Part II: Enum Classes for Actions

## Why Use Enum Classes?

Enum classes provide several advantages over string literals for action parameters:

1. **Type Safety**: IDE support with autocompletion and type checking
2. **Validation**: Automatic validation of valid action values
3. **Refactoring**: Safe renaming and restructuring of actions
4. **Documentation**: Clear definition of available actions in one place

## Defining Action Enums

```python
from enum import Enum

class HostAction(Enum):
    """Actions available for Docker host management."""
    LIST = "list"
    ADD = "add"
    EDIT = "edit" 
    REMOVE = "remove"
    TEST_CONNECTION = "test_connection"
    DISCOVER = "discover"
    PORTS = "ports"
    IMPORT_SSH = "import_ssh"
    CLEANUP = "cleanup"

class ContainerAction(Enum):
    """Actions available for Docker container management."""
    LIST = "list"
    INFO = "info"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    LOGS = "logs"
    REMOVE = "remove"

class ComposeAction(Enum):
    """Actions available for Docker Compose stack management."""
    LIST = "list"
    DISCOVER = "discover"
    VIEW = "view"
    DEPLOY = "deploy"
    UP = "up"
    DOWN = "down"
    RESTART = "restart"
    BUILD = "build"
    LOGS = "logs"
    MIGRATE = "migrate"
```

## Using Enums in Tool Parameters

```python
from typing import Annotated
from pydantic import Field

class DockerMCPServer:
    def __init__(self, config):
        self.app = FastMCP("Docker Context Manager")
        
        # Register tools using method registration pattern
        self.app.tool(
            self.docker_hosts,
            annotations={
                "title": "Docker Host Management", 
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": True,
            }
        )
    
    async def docker_hosts(
        self,
        action: Annotated[
            str | HostAction | None,  # Accept string, enum, or None
            Field(default=None, description="Action to perform (defaults to list if not provided)")
        ] = None,
        # ... other parameters
    ) -> dict[str, Any]:
    # Convert string to enum with validation
    try:
        if isinstance(action, str):
            action_enum = HostAction(action)  # Raises ValueError if invalid
        elif action is None:
            action_enum = HostAction.LIST  # Default action
        else:
            action_enum = action  # Already an enum
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid action '{action}'. Valid actions: {[a.value for a in HostAction]}"
        }
    
    # Use the validated enum
    return await handle_host_action(action_enum, **params)
```

## Enum Conversion Pattern

```python
def convert_string_to_enum(action: str | EnumType | None, enum_class: type[EnumType], default: EnumType) -> EnumType:
    """Convert string action to enum with validation."""
    if isinstance(action, str):
        try:
            return enum_class(action)
        except ValueError:
            valid_actions = [a.value for a in enum_class]
            raise ValueError(f"Invalid action '{action}'. Valid actions: {valid_actions}")
    elif action is None:
        return default
    else:
        return action  # Already the correct enum type

# Usage in tools
action_enum = convert_string_to_enum(action, HostAction, HostAction.LIST)
```

## Benefits in Practice

```python
# ✅ Type-safe action handling
async def handle_host_action(action: HostAction, **params):
    if action == HostAction.LIST:
        return await list_hosts()
    elif action == HostAction.ADD:
        return await add_host(**params)
    elif action == HostAction.PORTS:
        return await list_host_ports(**params)
    # IDE knows all possible enum values

# ✅ Clear documentation of available actions
def get_available_actions() -> list[str]:
    return [action.value for action in HostAction]

# ✅ Safe refactoring - renaming enum values updates everywhere
HostAction.TEST_CONNECTION  # IDE will find all usages
```

---

# Part III: Parameter Model Classes

## Why Parameter Models?

Parameter model classes provide:

1. **Centralized Validation**: All parameter validation in one place
2. **Type Safety**: Pydantic model validation and conversion
3. **Consistency**: Same parameter handling across all actions
4. **Reusability**: Models can be reused in tests and other code

## Defining Parameter Models

```python
from pydantic import BaseModel, Field
from typing import Literal

class DockerHostsParams(BaseModel):
    """Parameter model for docker_hosts tool."""
    action: HostAction
    host_id: str = ""
    ssh_host: str = ""
    ssh_user: str = ""
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH port number")
    ssh_key_path: str | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    compose_path: str | None = None
    appdata_path: str | None = None
    enabled: bool = True
    port: int = Field(default=0, ge=0, le=65535, description="Port number to check availability")
    cleanup_type: Literal["check", "safe", "moderate", "aggressive"] | None = None
    frequency: Literal["daily", "weekly", "monthly", "custom"] | None = None
    time: str | None = None
    ssh_config_path: str | None = None
    selected_hosts: str | None = None

class DockerContainerParams(BaseModel):
    """Parameter model for docker_container tool."""
    action: ContainerAction
    host_id: str = ""
    container_id: str = ""
    all_containers: bool = False
    limit: int = Field(default=20, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    follow: bool = False
    lines: int = Field(default=100, ge=1, le=10000)
    force: bool = False
    timeout: int = Field(default=10, ge=1, le=300)

class DockerComposeParams(BaseModel):
    """Parameter model for docker_compose tool."""
    action: ComposeAction
    host_id: str = ""
    stack_name: str = Field(
        default="",
        max_length=63,
        pattern=r"^$|^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Stack name (DNS-compliant: lowercase letters, numbers, hyphens; no underscores)"
    )
    compose_content: str = ""
    environment: dict[str, str] = Field(default_factory=dict)
    pull_images: bool = True
    recreate: bool = False
    follow: bool = False
    lines: int = Field(default=100, ge=1, le=10000)
    dry_run: bool = False
    options: dict[str, str] = Field(default_factory=dict)
    target_host_id: str = ""
    remove_source: bool = False
    skip_stop_source: bool = False
    start_target: bool = True
```

## Advanced Validation Patterns

The actual implementation uses sophisticated Pydantic validation patterns for enhanced type safety and data integrity:

```python
from pydantic import BaseModel, Field, computed_field, field_validator

def _validate_enum_action(value: Any, enum_class: type) -> Any:
    """Generic validator for enum action fields."""
    if isinstance(value, str):
        # Handle "EnumClass.VALUE" format
        if "." in value:
            enum_value = value.split(".")[-1].lower()
        else:
            enum_value = value.lower()

        # Match by value or name
        for action in enum_class:
            if action.value == enum_value or action.name.lower() == enum_value:
                return action
    elif isinstance(value, enum_class):
        return value

    # Let Pydantic handle the error if no match
    return value

class DockerHostsParams(BaseModel):
    """Parameter model with advanced validation patterns."""
    
    action: HostAction = Field(
        default=HostAction.LIST, 
        description="Action to perform (defaults to list if not provided)"
    )
    host_id: str = Field(default="", description="Host identifier")
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH port number")
    
    # Regex pattern validation for time fields
    time: str | None = Field(
        default=None,
        pattern=r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$",
        description="Cleanup schedule time in HH:MM format (24-hour)",
    )
    
    # Comma-separated list handling
    selected_hosts: str | None = Field(
        default=None, 
        description="Comma-separated list of hosts to select"
    )

    # Computed field for parsing comma-separated values
    @computed_field(return_type=list[str])
    @property
    def selected_hosts_list(self) -> list[str]:
        """Parse selected_hosts into a list."""
        if not self.selected_hosts:
            return []
        return [h.strip() for h in self.selected_hosts.split(",") if h.strip()]

    # Custom field validator for enum conversion
    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, v):
        """Validate action field to handle various enum input formats."""
        return _validate_enum_action(v, HostAction)

class DockerComposeParams(BaseModel):
    """Parameter model with DNS-compliant validation."""
    
    action: ComposeAction = Field(..., description="Action to perform")
    
    # Stack name with Docker Compose naming constraints
    stack_name: str = Field(
        default="",
        max_length=63,
        pattern=r"^$|^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Stack name (DNS-compliant: lowercase letters, numbers, hyphens; no underscores)",
    )
    
    lines: int = Field(
        default=100, 
        ge=1, 
        le=10000, 
        description="Number of log lines to retrieve"
    )

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, v):
        """Validate action field to handle various enum input formats."""
        return _validate_enum_action(v, ComposeAction)
```

## Using Parameter Models in Tools

```python
class DockerMCPServer:
    def __init__(self, config):
        self.app = FastMCP("Docker Context Manager")
        # Method registration pattern
        self.app.tool(self.docker_hosts, annotations={"title": "Docker Host Management"})
    
    async def docker_hosts(
        self,
        action: Annotated[str | HostAction | None, Field(default=None, description="...")] = None,
        host_id: Annotated[str, Field(default="", description="Host identifier")] = "",
        # ... all other parameters with defaults
    ) -> ToolResult | dict[str, Any]:
    # Parse and validate parameters using the parameter model
    try:
        # Convert string action to enum
        if isinstance(action, str):
            action_enum = HostAction(action)
        elif action is None:
            action_enum = HostAction.LIST
        else:
            action_enum = action

        # Create and validate parameter model
        params = DockerHostsParams(
            action=action_enum,
            host_id=host_id,
            ssh_host=ssh_host,
            ssh_user=ssh_user,
            # ... all parameters
        )
        
        # Use validated enum from parameter model
        action = params.action
    except Exception as e:
        return {
            "success": False,
            "error": f"Parameter validation failed: {str(e)}",
            "action": str(action) if action else "unknown",
        }

    # Delegate to service layer with validated parameters
    return await self.host_service.handle_action(
        action, **params.model_dump(exclude={"action"})
    )
```

## Model Validation Benefits

```python
# ✅ Automatic type conversion and validation
params = DockerHostsParams(
    action="add",  # Automatically converted to HostAction.ADD
    host_id="prod-server",
    ssh_port="22",  # Automatically converted to int
    tags=["production", "web"]  # List validation
)

# ✅ Field validation with constraints
class DockerContainerParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=1000)  # Must be 1-1000
    timeout: int = Field(default=10, ge=1, le=300)  # Must be 1-300
    
# ✅ Custom validation methods
class DockerHostsParams(BaseModel):
    @validator('ssh_port')
    def validate_ssh_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('SSH port must be between 1 and 65535')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v
```

---

# Part IV: Parameter Type Annotations

## The Problem

When using FastMCP, parameters can show up as "unknown" type in MCP clients, making it difficult for users and LLMs to understand what types of values are expected. This issue is caused by incorrect type annotation patterns that confuse FastMCP's Pydantic-based type introspection system.

## The Solution: Working Patterns (Actual Implementation)

### ✅ Action Parameters (Required)

For action parameters, use the enum union pattern:

```python
from typing import Annotated
from pydantic import Field
from .models.enums import ComposeAction

# Method registration pattern - self.app.tool(self.method_name)
async def docker_compose(
    # Action parameter - accepts string, enum, or None
    action: Annotated[str | ComposeAction, Field(description="Action to perform")],
    
    # Required for some actions, conditionally validated
    host_id: Annotated[str, Field(default="", description="Host identifier")] = "",
    stack_name: Annotated[str, Field(default="", description="Stack name")] = "",
) -> ToolResult | dict[str, Any]:
    pass
```

### ✅ Optional Parameters (Actual Patterns)

Real examples from the Docker MCP implementation:

```python
# Method registration pattern - self.app.tool(self.method_name)
async def docker_compose(
    # String parameters with defaults
    host_id: Annotated[str, Field(default="", description="Host identifier")] = "",
    stack_name: Annotated[str, Field(default="", description="Stack name")] = "",
    compose_content: Annotated[str, Field(default="", description="Docker Compose file content")] = "",
    
    # Optional union types (note: dict[str, str] | None pattern)
    environment: Annotated[
        dict[str, str] | None, Field(default=None, description="Environment variables")
    ] = None,
    options: Annotated[
        dict[str, str] | None, Field(default=None, description="Additional options")
    ] = None,
    
    # Boolean parameters with defaults
    pull_images: Annotated[bool, Field(default=True, description="Pull images before deploying")] = True,
    recreate: Annotated[bool, Field(default=False, description="Recreate containers")] = False,
    dry_run: Annotated[bool, Field(default=False, description="Perform a dry run")] = False,
    
    # Integer parameters with constraints
    lines: Annotated[
        int, Field(default=100, ge=1, le=10000, description="Number of log lines to retrieve")
    ] = 100,
    
    # Target host for migration operations
    target_host_id: Annotated[
        str, Field(default="", description="Target host ID for migration operations")
    ] = "",
) -> ToolResult | dict[str, Any]:
    pass
```

### ✅ Host Management Parameters (Complex Example)

```python
async def docker_hosts(
    # Action with enum union and default=None
    action: Annotated[
        str | HostAction | None,
        Field(default=None, description="Action to perform (defaults to list if not provided)")
    ] = None,
    
    # Core parameters
    host_id: Annotated[str, Field(default="", description="Host identifier")] = "",
    ssh_host: Annotated[str, Field(default="", description="SSH hostname or IP address")] = "",
    ssh_user: Annotated[str, Field(default="", description="SSH username")] = "",
    
    # Integer with constraints
    ssh_port: Annotated[
        int, Field(default=22, ge=1, le=65535, description="SSH port number")
    ] = 22,
    
    # Optional path (string | None pattern)
    ssh_key_path: Annotated[
        str, Field(default="", description="Path to SSH private key file")
    ] = "",
    
    # List with default_factory pattern
    tags: Annotated[list[str] | None, Field(default=None, description="Host tags")] = None,
    
    # Literal constraints for specific values
    cleanup_type: Annotated[
        Literal["check", "safe", "moderate", "aggressive"] | None,
        Field(default=None, description="Type of cleanup to perform"),
    ] = None,
    
    # Port number with validation
    port: Annotated[
        int, Field(default=0, ge=0, le=65535, description="Port number to check availability")
    ] = 0,
) -> ToolResult | dict[str, Any]:
    pass
```
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

---

# Part V: Complete Implementation Example

## Real-World Example: Docker MCP Server

### Tool Organization

```python
# Before: 27 separate tools
# Method registration pattern - self.app.tool(self.method_name)
async def list_stacks(): pass

# Method registration pattern - self.app.tool(self.method_name)  
async def deploy_stack(): pass

# Method registration pattern - self.app.tool(self.method_name)
async def manage_stack(): pass

# ... 24 more tools

# After: 3 consolidated tools with enum-based actions
# Method registration pattern - self.app.tool(self.method_name)
async def docker_compose(action: str | ComposeAction, ...): pass

# Method registration pattern - self.app.tool(self.method_name)
async def docker_container(action: str | ContainerAction, ...): pass

# Method registration pattern - self.app.tool(self.method_name)
async def docker_hosts(action: str | HostAction, ...): pass
```

### Complete Implementation: docker_compose Tool

Here's the actual implementation from server.py showing the real patterns used:

```python
from typing import Annotated, Any
from pydantic import Field
from fastmcp.tools.tool import ToolResult
from .models.enums import ComposeAction
from .models.params import DockerComposeParams

async def docker_compose(
    self,
    action: Annotated[str | ComposeAction, Field(description="Action to perform")],
    host_id: Annotated[str, Field(default="", description="Host identifier")] = "",
    stack_name: Annotated[str, Field(default="", description="Stack name")] = "",
    compose_content: Annotated[
        str, Field(default="", description="Docker Compose file content")
    ] = "",
    environment: Annotated[
        dict[str, str] | None, Field(default=None, description="Environment variables")
    ] = None,
    pull_images: Annotated[
        bool, Field(default=True, description="Pull images before deploying")
    ] = True,
    recreate: Annotated[bool, Field(default=False, description="Recreate containers")] = False,
    follow: Annotated[bool, Field(default=False, description="Follow log output")] = False,
    lines: Annotated[
        int, Field(default=100, ge=1, le=10000, description="Number of log lines to retrieve")
    ] = 100,
    dry_run: Annotated[
        bool, Field(default=False, description="Perform a dry run without making changes")
    ] = False,
    options: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Additional options for the operation"),
    ] = None,
    target_host_id: Annotated[
        str, Field(default="", description="Target host ID for migration operations")
    ] = "",
    remove_source: Annotated[
        bool, Field(default=False, description="Remove source stack after migration")
    ] = False,
    skip_stop_source: Annotated[
        bool, Field(default=False, description="Skip stopping source stack before migration")
    ] = False,
    start_target: Annotated[
        bool, Field(default=True, description="Start target stack after migration")
    ] = True,
) -> ToolResult | dict[str, Any]:
    """Consolidated Docker Compose stack management tool.

    Actions:
    • list: List stacks on a host
      - Required: host_id

    • deploy: Deploy a stack
      - Required: host_id, stack_name, compose_content
      - Optional: environment, pull_images, recreate

    • up/down/restart/build: Manage stack lifecycle
      - Required: host_id, stack_name
      - Optional: options

    • discover: Discover compose paths on a host
      - Required: host_id

    • logs: Get stack logs
      - Required: host_id, stack_name
      - Optional: follow, lines

    • migrate: Migrate stack between hosts
      - Required: host_id, target_host_id, stack_name
      - Optional: remove_source, skip_stop_source, start_target, dry_run
    """
    # Parse and validate parameters using the parameter model
    try:
        # Convert string action to enum
        if isinstance(action, str):
            action_enum = ComposeAction(action)
        else:
            action_enum = action

        params = DockerComposeParams(
            action=action_enum,
            host_id=host_id,
            stack_name=stack_name,
            compose_content=compose_content,
            environment=environment or {},
            pull_images=pull_images,
            recreate=recreate,
            follow=follow,
            lines=lines,
            dry_run=dry_run,
            options=options or {},
            target_host_id=target_host_id,
            remove_source=remove_source,
            skip_stop_source=skip_stop_source,
            start_target=start_target,
        )
        # Use validated enum from parameter model
        action = params.action
    except Exception as e:
        return {
            "success": False,
            "error": f"Parameter validation failed: {str(e)}",
            "action": str(action) if action else "unknown",
        }

    # Delegate to service layer for business logic
    return await self.stack_service.handle_action(
        action, **params.model_dump(exclude={"action"})
    )
```
    host_id: Annotated[str, Field(default="", description="Host identifier", min_length=1)] = "",
    ssh_host: Annotated[str, Field(default="", description="SSH hostname or IP address", min_length=1)] = "",
    ssh_user: Annotated[str, Field(default="", description="SSH username", min_length=1)] = "",
    
    # Optional parameters with explicit defaults in Field
    ssh_port: Annotated[int, Field(default=22, ge=1, le=65535, description="SSH port number")] = 22,
    ssh_key_path: Annotated[str, Field(default="", description="Path to SSH private key file")] = "",
    description: Annotated[str, Field(default="", description="Host description")] = "",
    tags: Annotated[list[str], Field(default_factory=list, description="Host tags")] = [],
    test_connection: Annotated[bool, Field(default=True, description="Test connection when adding host")] = True,
    
    # Action-specific parameters
    port: Annotated[int, Field(default=0, ge=1, le=65535, description="Port number for reservation operations")] = 0,
    cleanup_type: Annotated[str, Field(default="", description="Type of cleanup to perform")] = "",
    export_format: Annotated[str, Field(default="", description="Export format for port data")] = "",
    
    # Advanced validation examples
    schedule_time: Annotated[str, Field(default="", pattern=r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", description="Time to run cleanup in HH:MM format (24-hour)")] = ""
) -> dict[str, Any]:
    """Consolidated Docker hosts management tool.

    Actions:
    • list: List all configured Docker hosts
      - Required: none
      
    • add: Add a new Docker host
      - Required: host_id, ssh_host, ssh_user
      - Optional: ssh_port, ssh_key_path, description, tags, compose_path, enabled, test_connection
      
    • ports: List port mappings for a host
      - Required: host_id
      - Optional: include_stopped, export_format, filter_project, filter_range, filter_protocol, scan_available, suggest_next, use_cache
      
    • compose_path: Update host compose path
      - Required: host_id, compose_path
      
    • import_ssh: Import hosts from SSH config
      - Required: none
      - Optional: ssh_config_path, selected_hosts, compose_path_overrides, auto_confirm
      
    • reserve_port: Reserve a port on a host
      - Required: host_id, port, service_name
      - Optional: protocol, reserved_by, expires_days, notes
      
    • release_port: Release a port reservation
      - Required: host_id, port
      - Optional: protocol
    """
    
    # Validation
    valid_actions = ["list", "add", "ports", "compose_path", "import_ssh", "cleanup", "schedule", "reserve_port", "release_port"]
    if action not in valid_actions:
        return {
            "success": False,
            "error": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
        }
    
    try:
        # Route to appropriate handler
        if action == "list":
            return await self.list_docker_hosts()
        elif action == "add":
            # Validate required parameters for this action
            if not all([host_id, ssh_host, ssh_user]):
                return {
                    "success": False, 
                    "error": "host_id, ssh_host, and ssh_user are required for add action"
                }
            return await self.add_docker_host(host_id, ssh_host, ssh_user, ssh_port, ssh_key_path, description, tags)
        elif action == "ports":
            if not host_id:
                return {"success": False, "error": "host_id is required for ports action"}
            return await self.list_host_ports(host_id, export_format)
        elif action == "reserve_port":
            if not all([host_id, port]):
                return {"success": False, "error": "host_id and port are required for reserve_port action"}
            return await self.reserve_port(host_id, port)
        # ... handle other actions
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Action '{action}' failed: {str(e)}",
            "action": action
        }
```

## Parameter Strategies

### Required vs Optional Parameters

```python
# Method registration pattern - self.app.tool(self.method_name)
async def resource_manager(
    # Required for all actions - no default
    action: Annotated[Literal["list", "create", "update"], Field(description="Action to perform")],
    
    # Conditionally required - validate in function body
    resource_id: Annotated[str, Field(default="", description="Resource identifier")] = "",
    
    # Always optional with sensible defaults
    timeout: Annotated[int, Field(default=30, ge=1, le=300, description="Operation timeout")] = 30,
    force: Annotated[bool, Field(default=False, description="Force the operation")] = False
) -> dict:
    # Validate conditionally required parameters
    if action in ["update", "delete"] and not resource_id:
        return {"success": False, "error": f"resource_id is required for {action} action"}
```

### Parameter Grouping by Usage

```python
# Method registration pattern - self.app.tool(self.method_name)
async def container_manager(
    action: Annotated[Literal["list", "start", "stop", "logs"], Field(description="Action to perform")],
    
    # Core identification parameters
    host_id: Annotated[str, Field(default="", description="Docker host identifier")] = "",
    container_id: Annotated[str, Field(default="", description="Container identifier")] = "",
    
    # List-specific parameters
    all_containers: Annotated[bool, Field(default=False, description="Include stopped containers")] = False,
    limit: Annotated[int, Field(default=20, ge=1, le=1000, description="Max results")] = 20,
    
    # Logs-specific parameters  
    follow: Annotated[bool, Field(default=False, description="Follow log output")] = False,
    lines: Annotated[int, Field(default=100, ge=1, le=10000, description="Number of log lines")] = 100,
    
    # Operation parameters
    force: Annotated[bool, Field(default=False, description="Force the operation")] = False,
    timeout: Annotated[int, Field(default=10, ge=1, le=300, description="Timeout in seconds")] = 10
):
    pass
```

---

# Part IV: Validation and Error Handling

## Action Validation Pattern

```python
def validate_action(action: str, valid_actions: list[str]) -> tuple[bool, str]:
    """Validate action parameter."""
    if action not in valid_actions:
        return False, f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
    return True, ""

# Usage in tool
valid_actions = ["list", "create", "update", "delete"]
is_valid, error_msg = validate_action(action, valid_actions)
if not is_valid:
    return {"success": False, "error": error_msg}
```

## Parameter Validation by Action

```python
def validate_parameters_for_action(action: str, **params) -> tuple[bool, str]:
    """Validate required parameters for specific actions."""
    
    if action == "create":
        if not params.get("name"):
            return False, "name is required for create action"
    
    elif action in ["update", "delete"]:
        if not params.get("resource_id"):
            return False, f"resource_id is required for {action} action"
    
    elif action == "deploy":
        if not params.get("compose_content"):
            return False, "compose_content is required for deploy action"
    
    # Add range validations
    if params.get("port") and not (1 <= params["port"] <= 65535):
        return False, "port must be between 1 and 65535"
        
    return True, ""
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

---

# Part VI: Routing and Dispatch

## Service Layer Pattern (Actual Implementation)

The Docker MCP server uses a sophisticated service layer pattern for routing actions:

```python
class StackService:
    """Service layer for Docker Compose stack operations."""
    
    def __init__(self, config: DockerMCPConfig, context_manager: DockerContextManager, logs_service):
        self.config = config
        self.context_manager = context_manager
        self.logs_service = logs_service
        self.compose_manager = ComposeManager(config, context_manager)

    async def handle_action(self, action: ComposeAction, **params) -> ToolResult | dict[str, Any]:
        """Central dispatcher for all stack actions.
        
        The **params come from model_dump(exclude={"action"}) in server.py
        """
        
        # Route to specific action handlers
        if action == ComposeAction.LIST:
            return await self.list_stacks(params["host_id"])
        elif action == ComposeAction.DEPLOY:
            return await self.deploy_stack(
                params["host_id"], 
                params["stack_name"], 
                params["compose_content"],
                params.get("environment"),
                params.get("pull_images", True),
                params.get("recreate", False)
            )
        elif action == ComposeAction.UP:
            return await self.manage_stack(
                params["host_id"], 
                params["stack_name"], 
                "up", 
                params.get("options")
            )
        elif action == ComposeAction.DOWN:
            return await self.manage_stack(
                params["host_id"], 
                params["stack_name"], 
                "down", 
                params.get("options")
            )
        elif action == ComposeAction.LOGS:
            return await self.get_stack_logs(
                params["host_id"], 
                params["stack_name"],
                params.get("follow", False),
                params.get("lines", 100)
            )
        elif action == ComposeAction.MIGRATE:
            return await self.migrate_stack(
                params["host_id"],
                params["target_host_id"], 
                params["stack_name"],
                params.get("remove_source", False),
                params.get("skip_stop_source", False),
                params.get("start_target", True),
                params.get("dry_run", False)
            )
        else:
            return {
                "success": False,
                "error": f"Action '{action.value}' not implemented",
                "action": action.value
            }

    async def list_stacks(self, host_id: str) -> dict[str, Any]:
        """List Docker Compose stacks on a host."""
        # Implementation uses Docker SDK for efficiency
        try:
            client = await self.context_manager.get_client(host_id)
            if client is None:
                return {"success": False, "error": f"Could not connect to Docker on host {host_id}"}

            # Get all containers and group by compose project
            containers = await asyncio.to_thread(client.containers.list, all=True)
            # ... implementation details
            
        except Exception as e:
            logger.error("Failed to list stacks", host_id=host_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "host_id": host_id,
                "timestamp": datetime.now().isoformat(),
            }
```

## Tool → Service Delegation Pattern

```python
class DockerMCPServer:
    def __init__(self, config: DockerMCPConfig):
        # Initialize FastMCP app
        self.app = FastMCP("Docker Context Manager")
        
        # Initialize service layer
        self.stack_service = StackService(config, self.context_manager, self.logs_service)
        self.container_service = ContainerService(config, self.context_manager, self.logs_service)
        self.host_service = HostService(config, self.context_manager)
        
        # Register tools with method registration pattern
        self.app.tool(
            self.docker_compose,
            annotations={
                "title": "Docker Compose Management",
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": True,
            }
        )

    async def docker_compose(self, action: str | ComposeAction, **kwargs) -> ToolResult | dict[str, Any]:
        """MCP tool delegates to service layer."""
        # Parameter validation with model
        params = DockerComposeParams(action=action_enum, **kwargs)
        
        # Delegate to service layer for business logic
        return await self.stack_service.handle_action(
            params.action, **params.model_dump(exclude={"action"})
        )
```

## Action-Specific Method Routing

```python
class StackService:
    async def manage_stack(
        self, host_id: str, stack_name: str, action: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Unified stack lifecycle management with SSH execution."""
        
        # Build compose arguments for the action
        compose_args = self._build_compose_args(action, options or {})
        
        # Execute via SSH with compose file access
        result = await self._execute_compose_with_file(
            context_name, stack_name, compose_file_path, compose_args, None, timeout
        )
        
        return {
            "success": True,
            "message": f"Stack {stack_name} {action} completed successfully",
            "output": result,
            "execution_method": "ssh",
            "timestamp": datetime.now().isoformat(),
        }

    def _build_compose_args(self, action: str, options: dict[str, Any]) -> list[str]:
        """Build compose arguments based on action and options."""
        builders = {
            "up": self._build_up_args,
            "down": self._build_down_args,
            "restart": self._build_restart_args,
            "logs": self._build_logs_args,
            "build": self._build_build_args,
        }
        
        builder = builders.get(action)
        if builder:
            return builder(options)
        else:
            raise ValueError(f"Action '{action}' not supported")
```

## Complete Service Layer Implementation

The actual Docker MCP server shows sophisticated service layer patterns with full initialization and routing:

```python
class DockerMCPServer:
    """Complete server implementation with service layer."""
    
    def __init__(self, config: DockerMCPConfig, config_path: str | None = None):
        self.config = config
        self.logger = get_server_logger()
        
        # Initialize core managers
        self.context_manager = DockerContextManager(config)
        
        # Initialize service layer with dependencies
        from .services.logs import LogsService
        
        self.logs_service: LogsService = LogsService(config, self.context_manager)
        self.host_service: HostService = HostService(config, self.context_manager)
        self.container_service: ContainerService = ContainerService(
            config, self.context_manager, self.logs_service
        )
        self.stack_service: StackService = StackService(
            config, self.context_manager, self.logs_service
        )
        self.config_service = ConfigService(config, self.context_manager)
        self.cleanup_service = CleanupService(config)

class HostService:
    """Complete host service with action routing."""
    
    def __init__(self, config: DockerMCPConfig, context_manager: DockerContextManager):
        self.config = config
        self.context_manager = context_manager
        
    async def handle_action(self, action: HostAction, **params) -> dict[str, Any]:
        """Central dispatcher for all host actions.
        
        Note: **params comes from model_dump(exclude={"action"}) in the tool layer.
        """
        
        # Route to specific action handlers based on enum
        if action == HostAction.LIST:
            return await self.list_docker_hosts()
        elif action == HostAction.ADD:
            return await self.add_docker_host(
                params["host_id"],
                params["ssh_host"], 
                params["ssh_user"],
                params.get("ssh_port", 22),
                params.get("ssh_key_path"),
                params.get("description", ""),
                params.get("tags", []),
                params.get("compose_path"),
                params.get("enabled", True)
            )
        elif action == HostAction.PORTS:
            return await self.list_host_ports(params["host_id"])
        elif action == HostAction.TEST_CONNECTION:
            return await self.test_host_connection(params["host_id"])
        elif action == HostAction.DISCOVER:
            return await self.discover_host_paths(params["host_id"])
        elif action == HostAction.CLEANUP:
            return await self.cleanup_host(
                params["host_id"],
                params.get("cleanup_type", "check")
            )
        elif action == HostAction.IMPORT_SSH:
            return await self.import_ssh_config(
                params.get("ssh_config_path"),
                params.get("selected_hosts")
            )
        else:
            return {
                "success": False,
                "error": f"Action '{action.value}' not implemented",
                "action": action.value
            }
    
    async def list_docker_hosts(self) -> dict[str, Any]:
        """List all configured Docker hosts."""
        try:
            hosts_data = []
            for host_id, host_config in self.config.hosts.items():
                hosts_data.append({
                    "host_id": host_id,
                    "hostname": host_config.hostname,
                    "user": host_config.user,
                    "port": host_config.port,
                    "enabled": host_config.enabled,
                    "description": host_config.description,
                    "tags": host_config.tags
                })
            
            return {
                "success": True,
                "hosts": hosts_data,
                "total": len(hosts_data),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error("Failed to list hosts", error=str(e))
            return {
                "success": False,
                "error": f"Failed to list hosts: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
```

## Error Handling Pattern (Actual Implementation)

The Docker MCP server uses comprehensive error handling with parameter models:

```python
async def docker_compose(self, action: str | ComposeAction, **kwargs) -> ToolResult | dict[str, Any]:
    """Error handling with parameter model validation."""
    
    # Parse and validate parameters using the parameter model
    try:
        # Convert string action to enum with validation
        if isinstance(action, str):
            action_enum = ComposeAction(action)  # Raises ValueError if invalid
        else:
            action_enum = action

        # Parameter model handles all validation
        params = DockerComposeParams(
            action=action_enum,
            host_id=kwargs.get("host_id", ""),
            stack_name=kwargs.get("stack_name", ""),
            # ... all other parameters
        )
        
        # Use validated enum from parameter model
        action = params.action
        
    except ValueError as e:
        # Invalid enum value
        valid_actions = [a.value for a in ComposeAction]
        return {
            "success": False,
            "error": f"Invalid action '{action}'. Valid actions: {valid_actions}",
            "action": str(action) if action else "unknown",
        }
    except ValidationError as e:
        # Pydantic validation error
        return {
            "success": False,
            "error": f"Parameter validation failed: {str(e)}",
            "action": str(action) if action else "unknown",
        }
    except Exception as e:
        # Unexpected error during validation
        return {
            "success": False,
            "error": f"Parameter processing failed: {str(e)}",
            "action": str(action) if action else "unknown",
        }

    # Delegate to service layer with proper error context
    try:
        return await self.stack_service.handle_action(
            action, **params.model_dump(exclude={"action"})
        )
    except Exception as e:
        logger.error(
            "Service layer error", 
            action=action.value, 
            error=str(e), 
            exc_info=True
        )
        return {
            "success": False,
            "error": f"Action '{action.value}' failed: {str(e)}",
            "action": action.value,
            "timestamp": datetime.now().isoformat(),
        }
```

## Service Layer Error Handling

```python
class StackService:
    def _build_error_response(
        self, host_id: str, stack_name: str, action: str, error: str
    ) -> dict[str, Any]:
        """Build standardized error response."""
        logger.error(
            f"Failed to {action} stack",
            host_id=host_id,
            stack_name=stack_name,
            action=action,
            error=error,
        )
        return {
            "success": False,
            "error": error,
            "host_id": host_id,
            "stack_name": stack_name,
            "action": action,
            "timestamp": datetime.now().isoformat(),
        }

    async def deploy_stack(self, host_id: str, stack_name: str, compose_content: str, **kwargs):
        """Deploy with comprehensive error handling."""
        try:
            # Validate stack name
            if not self._validate_stack_name(stack_name):
                return self._build_error_response(
                    host_id, stack_name, "deploy",
                    f"Invalid stack name: {stack_name}. Must be alphanumeric with hyphens/underscores."
                )

            # Write compose file to persistent location
            compose_file_path = await self.compose_manager.write_compose_file(
                host_id, stack_name, compose_content
            )

            # Deploy using persistent compose file
            result = await self._deploy_stack_with_persistent_file(
                host_id, stack_name, compose_file_path, environment, pull_images, recreate
            )

            return result

        except (DockerCommandError, DockerContextError) as e:
            return self._build_error_response(host_id, stack_name, "deploy", str(e))
        except Exception as e:
            logger.error(
                "Unexpected deployment error", 
                host_id=host_id, 
                stack_name=stack_name, 
                error=str(e)
            )
            return self._build_error_response(
                host_id, stack_name, "deploy", f"Deployment failed: {e}"
            )
```

---

# Part VI: Best Practices

## 1. Action Naming

```python
# ✅ Good - Verb-based, clear actions
["list", "create", "update", "delete", "start", "stop", "restart"]

# ✅ Good - Domain-specific actions
["deploy", "scale", "migrate", "backup", "restore"]

# ❌ Avoid - Ambiguous or too generic
["manage", "handle", "process", "execute"]

# ❌ Avoid - Mixing abstraction levels  
["list", "get_detailed_info", "quick_start"]
```

## 2. Parameter Organization

```python
# Method registration pattern - self.app.tool(self.method_name)
async def consolidated_tool(
    # 1. Action parameter (always first)
    action: Annotated[Literal[...], Field(description="Action to perform")],
    
    # 2. Core required parameters (used by most actions)
    resource_id: Annotated[str, Field(description="Resource identifier")],
    
    # 3. Core optional parameters (used by most actions)
    name: Annotated[str, Field(default="", description="Resource name")] = "",
    
    # 4. Action-specific parameters (grouped by usage)
    # List parameters
    limit: Annotated[int, Field(default=20, description="Max results")] = 20,
    # Deploy parameters  
    compose_content: Annotated[str, Field(default="", description="Compose file")] = "",
    # Operation parameters
    force: Annotated[bool, Field(default=False, description="Force operation")] = False
):
    pass
```

## 3. Documentation Patterns

```python
# Method registration pattern - self.app.tool(self.method_name)
async def domain_manager(action, ...):
    """Consolidated domain management tool.

    Actions:
    • list: List all resources
      - Required: none
      
    • create: Create a new resource
      - Required: name
      - Optional: description, tags
      
    • update: Update resource
      - Required: resource_id
      - Optional: name, description
      
    • delete: Delete resource
      - Required: resource_id
      - Optional: force
      
    • deploy: Deploy resource
      - Required: resource_id, config
      - Optional: dry_run
    """
```

---

# Part VII: Migration Guide

## Converting Individual Tools to Consolidated

### Step 1: Identify Tool Groups
```python
# Group related tools by domain
container_tools = ["list_containers", "start_container", "stop_container", "get_container_logs"]
host_tools = ["list_hosts", "add_host", "remove_host", "test_host_connection"]
```

### Step 2: Design Action Parameter
```python
# Extract action from tool names
container_actions = ["list", "start", "stop", "logs"]  # Remove "container" prefix
host_actions = ["list", "add", "remove", "test"]      # Remove "host" prefix
```

### Step 3: Consolidate Parameters
```python
# Before - separate tools with duplicate parameters
async def start_container(host_id: str, container_id: str, timeout: int = 30): pass
async def stop_container(host_id: str, container_id: str, timeout: int = 30, force: bool = False): pass

# After - consolidated with shared parameters and proper annotations
async def container_manager(
    action: Annotated[Literal["start", "stop"], Field(description="Container action")],
    host_id: Annotated[str, Field(description="Docker host identifier")],
    container_id: Annotated[str, Field(description="Container identifier")],
    timeout: Annotated[int, Field(default=30, ge=1, le=300, description="Operation timeout")] = 30,
    force: Annotated[bool, Field(default=False, description="Force the operation")] = False  # Used by stop, ignored by start
): pass
```

### Step 4: Implement Routing
```python
async def container_manager(action: str, **params):
    # Map actions to original functions
    action_map = {
        "list": original_list_containers,
        "start": original_start_container,
        "stop": original_stop_container,
        "logs": original_get_container_logs
    }
    
    handler = action_map.get(action)
    return await handler(**params)
```

---

# Part VIII: Troubleshooting

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

## Common Issues

1. **Too Many Parameters**: If you have >15 parameters, consider splitting into multiple consolidated tools
2. **Parameter Conflicts**: When actions need mutually exclusive parameters, use validation in the function body
3. **Action Overlap**: Avoid having similar actions across different consolidated tools
4. **Validation Complexity**: If validation logic becomes too complex, consider separate validation functions

## Performance Considerations

- **Token Efficiency**: Consolidated tools use significantly fewer tokens than individual tools
- **Context Overhead**: Each tool adds ~400-500 tokens to context - consolidation reduces this multiplicatively
- **Parameter Parsing**: More parameters per tool, but FastMCP handles this efficiently
- **Route Dispatch**: Minimal overhead compared to context token savings

---

# Summary

## Key Takeaways

### For Consolidated Action-Parameter Pattern:
- **Massive token efficiency**: 2.6x more efficient than individual tools
- **Better organization**: Logical grouping of related operations  
- **Cleaner interfaces**: Fewer tools in MCP client listings
- **Easier maintenance**: Centralized validation and error handling
- **Consistent UX**: Uniform parameter patterns across actions

### For Parameter Type Annotations (Updated):
1. **Action Parameters**: `Annotated[str | EnumAction | None, Field(default=None, description="...")] = None`
2. **Required Parameters**: `Annotated[Type, Field(description="...")]` (no default)
3. **Optional Parameters**: `Annotated[Type, Field(default=value, description="...")] = value`
4. **Union Types**: Use `Type | None` patterns for optional complex types (dict, list)
5. **Parameter Models**: Use Pydantic models for validation and type conversion
6. **Enum Classes**: Use proper Enum classes for actions, not Literal types

### For Documentation Format:
- **Use bullet points**: • for main actions, - for sub-bullets
- **Clear parameter organization**: Separate Required and Optional sections
- **Consistent formatting**: Same format across all consolidated tools

### For Implementation Architecture:
- **Service Layer**: Business logic in service classes with handle_action() methods
- **Parameter Models**: Pydantic models for validation and type conversion
- **Error Handling**: Consistent dict-based error responses with success: False
- **Enum Actions**: Type-safe action enums instead of string literals

Together, these patterns create FastMCP servers that are:
- **Token-efficient** (critical for context limits) - 2.6x more efficient than individual tools
- **User-friendly** (clean, discoverable interfaces with proper type introspection)
- **Type-safe** (enum validation and parameter model validation)
- **Maintainable** (service layer architecture with centralized logic)
- **Scalable** (easy to add new actions via enums and service methods)

This approach is especially valuable for domain-rich APIs like Docker management where you have many related operations that share common parameters and validation logic. The Docker MCP server demonstrates these patterns in production with 3 consolidated tools handling 27+ operations efficiently.
