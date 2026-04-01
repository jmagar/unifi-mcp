# Multi-stage build for UniFi MCP Server
# Builder stage: install deps and compile
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install -e .

# Copy application code
COPY unifi_mcp/ ./unifi_mcp/

# Runtime stage: minimal image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/sh --uid 1000 unifi

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --from=builder /build/unifi_mcp/ ./unifi_mcp/
COPY pyproject.toml ./

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set ownership
RUN chown -R unifi:unifi /app

# Switch to non-root user
USER unifi

# Expose the MCP port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8001/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "unifi_mcp.main"]
