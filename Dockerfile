# Single-stage build for UniFi MCP Server
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash unifi

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using pip
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Change ownership to unifi user
RUN chown -R unifi:unifi /app

# Switch to non-root user
USER unifi

# Expose the default MCP port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command
CMD ["python", "-m", "unifi_mcp.main"]
