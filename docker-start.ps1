# Docker startup script for notes-mcp

Write-Host "🐳 Starting Notes MCP Docker Containers..." -ForegroundColor Cyan
Write-Host ""

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down

# Rebuild images to ensure templates are created
Write-Host ""
Write-Host "Rebuilding Docker images..." -ForegroundColor Yellow
docker compose build

# Start services
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
docker compose up -d

# Show status
Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host ""
docker compose ps

Write-Host ""
Write-Host "📝 Web interface: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🔧 MCP Server HTTP: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker compose logs -f" -ForegroundColor Gray
Write-Host "To stop: docker compose down" -ForegroundColor Gray
