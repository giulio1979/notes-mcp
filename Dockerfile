# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install mcp>=1.16.0 \
                python-dateutil>=2.8.2 \
                aiofiles>=23.2.1 \
                rapidfuzz>=3.5.2 \
                flask>=3.0.0 \
                markdown>=3.5.0

# Create data directory
RUN mkdir -p /app/data

# Create templates directory and generate templates
RUN mkdir -p /app/src/templates && \
    python -c "from src.web_server import create_templates; create_templates()"

# Expose ports
# Port 8000 for MCP server (SSE/HTTP transports)
# Port 5000 for web interface
EXPOSE 8000 5000

# Health check for web server
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000').read()" || exit 1

# Default command runs the MCP server with stdio
# Override with docker-compose or docker run command for different transports
CMD ["python", "-m", "src.server"]
