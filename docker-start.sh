#!/bin/bash

# Docker startup script for notes-mcp

echo "🐳 Starting Notes MCP Docker Containers..."
echo ""

# Stop any existing containers
echo "Stopping existing containers..."
docker compose down

# Rebuild images to ensure templates are created
echo ""
echo "Rebuilding Docker images..."
docker compose build

# Start services
echo ""
echo "Starting services..."
docker compose up -d

# Show status
echo ""
echo "✅ Services started!"
echo ""
docker compose ps

echo ""
echo "📝 Web interface: http://localhost:5000"
echo "🔧 MCP Server HTTP: http://localhost:8000"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
