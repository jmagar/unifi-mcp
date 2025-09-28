# FastMCP Middleware Patterns for Docker MCP

> Comprehensive guide to implementing sophisticated middleware patterns in FastMCP servers using the Docker MCP architecture as a reference implementation.

## Overview

FastMCP middleware provides a powerful pipeline for implementing cross-cutting concerns in MCP servers. Docker MCP demonstrates advanced middleware patterns including logging, error handling, performance monitoring, and rate limiting using FastMCP's class-based middleware system.

### Core Benefits

- **Request/Response Interception**: Full control over MCP message flow
- **Cross-cutting Concerns**: Centralized logging, monitoring, and security
- **Pipeline Architecture**: Composable middleware chain with proper ordering
- **Context Preservation**: Maintain request context throughout the chain
- **Error Handling**: Comprehensive error tracking and recovery

## Architecture Overview

### Middleware Chain Pattern

Docker MCP implements a sophisticated middleware chain where each middleware can:

1. **Pre-process requests** - Inspect and modify incoming messages
2. **Execute downstream** - Continue the chain or short-circuit
3. **Post-process responses** - Transform results and collect metrics
4. **Handle errors** - Catch, log, and re-raise exceptions properly

```
Client Request → Error → Rate Limit → Timing → Logging → Handler
              ↖                                           ↗
               Post-process ← Post-process ← Post-process ← Response
```

### FastMCP Class-Based Pattern

All middleware extends FastMCP's `Middleware` base class:

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext

class MyMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        # Pre-processing
        start_time = time.perf_counter()
        
        try:
            # Continue chain
            result = await call_next(context)
            
            # Post-processing
            duration = time.perf_counter() - start_time
            return result
            
        except Exception as e:
            # Error handling
            self.logger.error("Request failed", error=str(e))
            raise  # Always re-raise to preserve context
```

## Core Implementation Patterns

### 1. Logging Middleware Pattern

Comprehensive request/response logging with sensitive data sanitization:

```python
class LoggingMiddleware(Middleware):
    """FastMCP middleware for comprehensive request/response logging."""
    
    def __init__(self, include_payloads: bool = True, max_payload_length: int = 1000):
        self.logger = get_middleware_logger()
        self.include_payloads = include_payloads
        self.max_payload_length = max_payload_length

    async def on_message(self, context: MiddlewareContext, call_next):
        start_time = time.time()
        
        # Log request with sanitized parameters
        log_data = {
            "method": context.method,
            "source": context.source,
            "message_type": context.type,
            "timestamp": context.timestamp,
        }
        
        if self.include_payloads and hasattr(context.message, "__dict__"):
            log_data["params"] = self._sanitize_message(context.message)
        
        self.logger.info("MCP request started", **log_data)
        
        try:
            result = await call_next(context)
            
            # Log successful completion
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self.logger.info(
                "MCP request completed",
                method=context.method,
                success=True,
                duration_ms=duration_ms,
            )
            return result
            
        except Exception as e:
            # Log error with full context
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self.logger.error(
                "MCP request failed",
                method=context.method,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,  # Include stack trace
            )
            raise  # Always re-raise to preserve FastMCP error handling
```

#### Sensitive Data Sanitization Pattern

```python
def _sanitize_message(self, message: Any) -> dict[str, Any]:
    """Sanitize message data for safe logging."""
    if not hasattr(message, "__dict__"):
        return {"message": str(message)[:self.max_payload_length]}
    
    sanitized = {}
    
    for key, value in message.__dict__.items():
        if key.startswith("_"):
            continue
            
        # Redact sensitive information
        if self._is_sensitive_field(key):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str):
            # Truncate long strings
            if len(value) > self.max_payload_length:
                sanitized[key] = value[:self.max_payload_length] + "... [TRUNCATED]"
            else:
                sanitized[key] = value
        elif isinstance(value, dict | list):
            str_value = str(value)
            if len(str_value) > self.max_payload_length:
                sanitized[key] = str_value[:self.max_payload_length] + "... [TRUNCATED]"
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value
    
    return sanitized

def _is_sensitive_field(self, field_name: str) -> bool:
    """Check if field contains sensitive data that should be redacted."""
    sensitive_keywords = [
        "password", "passwd", "pwd",
        "token", "access_token", "refresh_token", "api_token",
        "key", "api_key", "private_key", "secret_key", "ssh_key",
        "identity_file", "cert", "certificate",
        "secret", "client_secret", "auth_secret",
        "credential", "auth", "authorization",
    ]
    
    field_lower = field_name.lower()
    return any(sensitive in field_lower for sensitive in sensitive_keywords)
```

### 2. Error Handling Middleware Pattern

Comprehensive error tracking with statistics and proper context preservation:

```python
class ErrorHandlingMiddleware(Middleware):
    """FastMCP middleware for comprehensive error handling and tracking."""
    
    def __init__(self, include_traceback: bool = True, track_error_stats: bool = True):
        self.logger = get_middleware_logger()
        self.include_traceback = include_traceback
        self.track_error_stats = track_error_stats
        
        # Error statistics tracking
        self.error_stats: dict[str, int] = defaultdict(int)
        self.method_errors: dict[str, int] = defaultdict(int)

    async def on_message(self, context: MiddlewareContext, call_next):
        try:
            return await call_next(context)
        except Exception as e:
            await self._handle_error(e, context)
            raise  # Always re-raise to preserve FastMCP error handling

    async def _handle_error(self, error: Exception, context: MiddlewareContext) -> None:
        error_type = type(error).__name__
        method = context.method
        
        # Update statistics if enabled
        if self.track_error_stats and method is not None:
            error_key = f"{error_type}:{method}"
            self.error_stats[error_key] += 1
            self.method_errors[method] += 1
        
        # Create comprehensive error log
        error_data: dict[str, Any] = {
            "error_type": error_type,
            "error_message": str(error),
            "method": method,
            "source": context.source,
            "message_type": context.type,
            "timestamp": context.timestamp,
        }
        
        # Add statistics if tracking is enabled
        if self.track_error_stats and method is not None:
            error_data.update({
                "error_occurrence_count": self.error_stats[f"{error_type}:{method}"],
                "method_error_count": self.method_errors[method],
                "total_error_types": len(self.error_stats),
            })
        
        # Log with appropriate level based on error type
        if self._is_critical_error(error):
            self.logger.critical(
                "Critical error in MCP request", 
                **error_data, 
                exc_info=self.include_traceback
            )
        elif self._is_warning_level_error(error):
            self.logger.warning(
                "Warning-level error in MCP request",
                **error_data,
                exc_info=False,
            )
        else:
            self.logger.error(
                "Error in MCP request", 
                **error_data, 
                exc_info=self.include_traceback
            )
```

#### Error Categorization Pattern

```python
def _is_critical_error(self, error: Exception) -> bool:
    """Determine if error should be logged as critical."""
    critical_types = (SystemError, MemoryError, RecursionError, KeyboardInterrupt, SystemExit)
    return isinstance(error, critical_types)

def _is_warning_level_error(self, error: Exception) -> bool:
    """Determine if error should be logged as warning instead of error."""
    warning_types = (TimeoutError, ConnectionError, FileNotFoundError, PermissionError)
    return isinstance(error, warning_types)

def get_error_statistics(self) -> dict[str, Any]:
    """Get comprehensive error statistics."""
    if not self.track_error_stats:
        return {"error_tracking": "disabled"}
    
    total_errors = sum(self.error_stats.values())
    
    # Get top error types
    top_errors = sorted(self.error_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get methods with most errors
    top_error_methods = sorted(self.method_errors.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_errors": total_errors,
        "unique_error_types": len(self.error_stats),
        "top_errors": top_errors,
        "top_error_methods": top_error_methods,
        "error_distribution": dict(self.error_stats),
    }
```

### 3. Timing Middleware Pattern

High-precision performance monitoring with statistics tracking:

```python
class TimingMiddleware(Middleware):
    """FastMCP middleware for comprehensive request timing and performance monitoring."""
    
    def __init__(
        self,
        slow_request_threshold_ms: float = 5000.0,
        track_statistics: bool = True,
        max_history_size: int = 1000,
    ):
        self.logger = get_middleware_logger()
        self.slow_threshold_ms = slow_request_threshold_ms
        self.track_statistics = track_statistics
        self.max_history_size = max_history_size
        
        # Timing statistics using deque for efficient sliding window
        self.request_times: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.method_stats: dict[str, dict[str, Any]] = defaultdict(dict)
        self.total_requests = 0
        self.slow_requests = 0

    async def on_message(self, context: MiddlewareContext, call_next):
        # Use perf_counter for high precision timing
        start_time = time.perf_counter()
        method = context.method
        success = False
        
        try:
            result = await call_next(context)
            success = True
            return result
        except Exception:
            success = False
            raise
        finally:
            # Calculate timing metrics
            end_time = time.perf_counter()
            duration_seconds = end_time - start_time
            duration_ms = duration_seconds * 1000
            
            # Update statistics if enabled
            if self.track_statistics and method is not None:
                await self._update_statistics(method, duration_ms, success)
            
            # Log timing information
            if method is not None:
                await self._log_timing(method, duration_ms, success, context)
```

#### Performance Statistics Pattern

```python
async def _update_statistics(self, method: str, duration_ms: float, success: bool) -> None:
    """Update internal timing statistics."""
    self.total_requests += 1
    
    # Track slow requests
    if duration_ms > self.slow_threshold_ms:
        self.slow_requests += 1
    
    # Add to history with sliding window
    self.request_times[method].append({
        "duration_ms": duration_ms, 
        "success": success, 
        "timestamp": time.time()
    })
    
    # Update method statistics
    method_times = [req["duration_ms"] for req in self.request_times[method]]
    
    if method_times:
        self.method_stats[method] = {
            "count": len(method_times),
            "avg_ms": sum(method_times) / len(method_times),
            "min_ms": min(method_times),
            "max_ms": max(method_times),
            "success_rate": sum(1 for req in self.request_times[method] if req["success"]) / len(method_times),
            "slow_count": sum(1 for t in method_times if t > self.slow_threshold_ms),
        }

async def _log_timing(self, method: str, duration_ms: float, success: bool, context: MiddlewareContext) -> None:
    """Log timing information with appropriate level and detail."""
    log_data = {
        "method": method,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "source": context.source,
        "message_type": context.type,
    }
    
    # Add performance context if statistics are enabled
    if self.track_statistics and method in self.method_stats:
        stats = self.method_stats[method]
        log_data.update({
            "avg_duration_ms": round(stats["avg_ms"], 2),
            "method_request_count": stats["count"],
            "success_rate": round(stats["success_rate"], 3),
        })
    
    # Log based on performance characteristics
    if duration_ms > self.slow_threshold_ms:
        self.logger.warning(
            "Slow request detected",
            **log_data,
            slow_threshold_ms=self.slow_threshold_ms,
            performance_impact="high",
        )
    elif duration_ms > self.slow_threshold_ms * 0.5:
        self.logger.info("Moderate duration request", **log_data, performance_impact="medium")
    else:
        self.logger.debug("Request completed", **log_data, performance_impact="low")
```

### 4. Rate Limiting Middleware Pattern

Token bucket algorithm with per-client rate limiting:

```python
class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()  # Async-safe locking
    
    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket."""
        async with self._lock:
            now = time.time()
            
            # Refill bucket based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimitingMiddleware(Middleware):
    """FastMCP middleware for request rate limiting using token bucket algorithm."""
    
    def __init__(
        self,
        max_requests_per_second: float = 10.0,
        burst_capacity: int | None = None,
        client_id_func: Callable[[MiddlewareContext], str] | None = None,
        enable_global_limit: bool = True,
        per_method_limits: dict[str, float] | None = None,
        cleanup_interval: float = 300.0,  # 5 minutes
    ):
        self.logger = get_middleware_logger()
        self.max_requests_per_second = max_requests_per_second
        self.burst_capacity = burst_capacity or int(max_requests_per_second * 2)
        self.client_id_func = client_id_func or self._default_client_id
        self.enable_global_limit = enable_global_limit
        self.per_method_limits = per_method_limits or {}
        self.cleanup_interval = cleanup_interval
        
        # Client token buckets
        self.client_buckets: dict[str, TokenBucket] = {}
        self.method_buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        
        # Statistics
        self.rate_limit_hits = 0
        self.total_requests = 0
        self.client_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"requests": 0, "rate_limited": 0, "last_request": time.time()}
        )
        
        self.last_cleanup = time.time()

    async def on_message(self, context: MiddlewareContext, call_next):
        client_id = self.client_id_func(context)
        method = context.method
        
        self.total_requests += 1
        self.client_stats[client_id]["requests"] += 1
        self.client_stats[client_id]["last_request"] = time.time()
        
        # Check global rate limit
        if self.enable_global_limit:
            if not await self._check_client_rate_limit(client_id):
                await self._handle_rate_limit_exceeded(client_id, method or "unknown", "global")
                return
        
        # Check per-method rate limit
        if method and method in self.per_method_limits:
            if not await self._check_method_rate_limit(client_id, method):
                await self._handle_rate_limit_exceeded(client_id, method, "method")
                return
        
        # Perform periodic cleanup
        await self._periodic_cleanup()
        
        return await call_next(context)
```

#### Rate Limiting Helpers

```python
async def _check_client_rate_limit(self, client_id: str) -> bool:
    """Check if client is within global rate limit."""
    if client_id not in self.client_buckets:
        self.client_buckets[client_id] = TokenBucket(
            capacity=self.burst_capacity, 
            refill_rate=self.max_requests_per_second
        )
    
    return await self.client_buckets[client_id].consume()

async def _handle_rate_limit_exceeded(self, client_id: str, method: str, limit_type: str) -> None:
    """Handle rate limit exceeded scenario."""
    self.rate_limit_hits += 1
    self.client_stats[client_id]["rate_limited"] += 1
    
    # Log rate limit hit
    self.logger.warning(
        "Rate limit exceeded",
        client_id=client_id,
        method=method,
        limit_type=limit_type,
        total_rate_limits=self.rate_limit_hits,
    )
    
    # Raise MCP error
    error_message = f"Rate limit exceeded for {limit_type} limits. Try again later."
    raise McpError(ErrorData(code=-32000, message=error_message))

async def _periodic_cleanup(self) -> None:
    """Clean up inactive client buckets to prevent memory leaks."""
    now = time.time()
    
    if now - self.last_cleanup < self.cleanup_interval:
        return
    
    self.last_cleanup = now
    inactive_threshold = now - self.cleanup_interval * 2
    
    # Clean up inactive clients
    inactive_clients = [
        client_id for client_id, stats in self.client_stats.items()
        if stats["last_request"] < inactive_threshold
    ]
    
    for client_id in inactive_clients:
        self.client_buckets.pop(client_id, None)
        self.client_stats.pop(client_id, None)
        
        for method_buckets in self.method_buckets.values():
            method_buckets.pop(client_id, None)
```

## Advanced Patterns

### Context Enrichment Pattern

Automatic context enhancement for all middleware:

```python
async def context_enrichment_middleware(ctx: MiddlewareContext, next_handler) -> Any:
    """Automatically enrich context for downstream middleware."""
    import contextvars
    
    # Create context variables that persist through async calls
    request_id = contextvars.ContextVar('request_id', default=None)
    operation_id = contextvars.ContextVar('operation_id', default=None)
    
    # Set context for this request chain
    request_id.set(getattr(ctx, "request_id", f"req_{int(time.time())}"))
    operation_id.set(getattr(ctx, "method", "unknown_operation"))
    
    try:
        return await next_handler(ctx)
    except Exception as e:
        # Context variables automatically available in exception handlers
        await ctx.error(
            "Error with full context",
            error=str(e),
            request_id=request_id.get(),
            operation_id=operation_id.get(),
            context_preserved=True
        )
        raise
```

### Metrics Collection Pattern

Comprehensive metrics tracking for monitoring systems:

```python
def _record_timing(duration: float, success: bool, method: str) -> None:
    """Record timing metrics for monitoring systems."""
    # Debug logging (always available)
    logger.debug("Request timing", 
                duration_seconds=duration, 
                success=success, 
                method=method)
    
    # Metrics system integration (if available)
    if hasattr(metrics, 'record_request_duration'):
        metrics.record_request_duration(duration, success, method)
    
    # Prometheus metrics (if configured)
    if prometheus_metrics:
        prometheus_metrics.request_duration.observe(duration)
        prometheus_metrics.request_count.inc(labels={
            'success': str(success).lower(),
            'method': method
        })
```

## Server Integration

### Middleware Registration Pattern

Docker MCP registers middleware in a specific order for optimal functionality:

```python
def _configure_middleware(self) -> None:
    """Configure FastMCP middleware stack."""
    # Add middleware in logical order (first added = first executed)
    
    # 1. Error handling first to catch all errors
    self.app.add_middleware(
        ErrorHandlingMiddleware(
            include_traceback=os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG",
            track_error_stats=True,
        )
    )
    
    # 2. Rate limiting to protect against abuse
    rate_limit = float(os.getenv("RATE_LIMIT_PER_SECOND", "50.0"))
    self.app.add_middleware(
        RateLimitingMiddleware(
            max_requests_per_second=rate_limit,
            burst_capacity=int(rate_limit * 2),
        )
    )
    
    # 3. Timing middleware to monitor performance
    slow_threshold = float(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "5000.0"))
    self.app.add_middleware(
        TimingMiddleware(
            slow_request_threshold_ms=slow_threshold, 
            track_statistics=True
        )
    )
    
    # 4. Logging middleware last to log everything (including middleware processing)
    self.app.add_middleware(
        LoggingMiddleware(
            include_payloads=os.getenv("LOG_INCLUDE_PAYLOADS", "true").lower() == "true",
            max_payload_length=int(os.getenv("LOG_MAX_PAYLOAD_LENGTH", "1000")),
        )
    )
```

### Middleware Order Considerations

```python
# Optimal middleware order for Docker MCP:
[
    ErrorHandlingMiddleware,    # First: Catch all errors from downstream
    RateLimitingMiddleware,     # Second: Security before processing
    TimingMiddleware,           # Third: Time actual processing
    LoggingMiddleware,          # Last: Log everything including middleware
]

# Request flow:
# Client → Error → Rate Limit → Timing → Logging → Handler
# Client ← Error ← Rate Limit ← Timing ← Logging ← Response
```

## Best Practices

### 1. Error Preservation

**Always re-raise exceptions** to preserve FastMCP error handling:

```python
try:
    result = await call_next(context)
    return result
except Exception as e:
    # Log error, update stats, etc.
    self.logger.error("Error occurred", error=str(e))
    raise  # Critical: Always re-raise
```

### 2. Async-Safe Operations

Use proper async patterns for shared resources:

```python
# Use asyncio.Lock for async-safe operations
self._lock = asyncio.Lock()

async def consume(self, tokens: int = 1) -> bool:
    async with self._lock:
        # Thread-safe operations here
        return True
```

### 3. Memory Management

Implement cleanup patterns to prevent memory leaks:

```python
# Use deque with maxlen for sliding windows
self.request_times: dict[str, deque] = defaultdict(
    lambda: deque(maxlen=max_history_size)
)

# Periodic cleanup of inactive resources
async def _periodic_cleanup(self) -> None:
    if now - self.last_cleanup < self.cleanup_interval:
        return
    # Remove inactive clients/resources
```

### 4. High-Precision Timing

Use `perf_counter` for accurate performance measurements:

```python
start_time = time.perf_counter()  # Not time.time()
# ... operation ...
duration = time.perf_counter() - start_time
duration_ms = round(duration * 1000, 2)  # Round to appropriate precision
```

### 5. Sensitive Data Handling

Always sanitize logs to prevent data leaks:

```python
def _sanitize_message(self, message: Any) -> dict[str, Any]:
    """Sanitize message data for safe logging."""
    # Check for sensitive fields and redact
    if self._is_sensitive_field(key):
        sanitized[key] = "[REDACTED]"
    # Truncate long values
    elif len(value) > self.max_payload_length:
        sanitized[key] = value[:self.max_payload_length] + "... [TRUNCATED]"
```

## Testing Strategies

### Unit Testing Middleware

```python
import pytest
from fastmcp.server.middleware import MiddlewareContext

@pytest.mark.asyncio
async def test_logging_middleware():
    middleware = LoggingMiddleware()
    context = MiddlewareContext(
        method="test_method",
        source="client",
        type="request",
        message=TestMessage(),
        timestamp="2024-01-01T00:00:00Z"
    )
    
    async def mock_call_next(ctx):
        return "test_result"
    
    result = await middleware.on_message(context, mock_call_next)
    assert result == "test_result"
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_middleware_chain():
    app = FastMCP("test")
    app.add_middleware(ErrorHandlingMiddleware())
    app.add_middleware(TimingMiddleware())
    app.add_middleware(LoggingMiddleware())
    
    @app.tool
    def test_tool() -> str:
        return "success"
    
    # Test that middleware chain processes requests correctly
    result = await app.call_tool("test_tool", {})
    assert result == "success"
```

## Environment Configuration

Docker MCP uses environment variables for middleware configuration:

```bash
# Logging configuration
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
LOG_INCLUDE_PAYLOADS=true              # Include request/response payloads
LOG_MAX_PAYLOAD_LENGTH=1000            # Maximum payload length before truncation

# Rate limiting configuration
RATE_LIMIT_PER_SECOND=50.0            # Global rate limit (requests/second)

# Performance monitoring
SLOW_REQUEST_THRESHOLD_MS=5000.0       # Threshold for slow request alerts
```

## Conclusion

Docker MCP's middleware implementation demonstrates sophisticated patterns for building robust, observable, and secure MCP servers. The combination of logging, error handling, timing, and rate limiting provides a solid foundation for production FastMCP deployments.

Key takeaways:

- **Use class-based middleware** extending FastMCP's `Middleware` base class
- **Always re-raise exceptions** to preserve error context
- **Implement async-safe patterns** with proper locking
- **Track comprehensive statistics** for observability
- **Sanitize sensitive data** in logs and responses
- **Order middleware carefully** for optimal functionality
- **Use high-precision timing** with `perf_counter`
- **Implement cleanup patterns** to prevent memory leaks

This architecture scales effectively for complex Docker infrastructure management while providing the observability and reliability needed for production systems.