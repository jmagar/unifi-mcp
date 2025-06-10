FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user
RUN groupadd --gid 1000 mcpuser && \
    useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 6977

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:6977/health || exit 1

# Set default environment variables
ENV UNIFI_MCP_HOST=0.0.0.0
ENV UNIFI_MCP_PORT=6977
ENV UNIFI_MCP_TRANSPORT=sse

# Run the server via entrypoint
CMD ["./entrypoint.sh"] 