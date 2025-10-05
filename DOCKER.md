# Docker Deployment Guide

This guide explains how to deploy the Notes MCP server using Docker for remote access.

## Quick Start

### Using Helper Scripts

**Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**Windows (PowerShell):**
```powershell
.\docker-start.ps1
```

### Manual Start

```bash
# Build and start services
docker compose build
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Services

The Docker Compose setup includes two services:

### 1. MCP Server (HTTP)
- **Container:** `notes-mcp-server`
- **Port:** 8000
- **Transport:** streamable-http
- **Endpoint:** http://localhost:8000
- **Use case:** Remote access via HTTP API
- **Data:** Stored in `./data/`

### 2. Web Interface
- **Container:** `notes-mcp-web`
- **Port:** 5000
- **URL:** http://localhost:5000
- **Features:** 
  - Browse all projects
  - View notes with version history
  - Full-text fuzzy search
  - Generate deep links for sharing
  - Rebuild search index

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   MCP Clients   │────────▶│  MCP Server     │
│  (HTTP/Remote)  │         │  Port 8000      │
└─────────────────┘         └─────────────────┘
                                    │
                                    │ shares data
                                    ▼
┌─────────────────┐         ┌─────────────────┐
│   Web Browser   │────────▶│  Web Interface  │
│                 │         │  Port 5000      │
└─────────────────┘         └─────────────────┘
                                    │
                                    │
                                    ▼
                             ┌─────────────────┐
                             │  ./data/        │
                             │  (local folder) │
                             └─────────────────┘
```

## Configuration

### Environment Variables

The services can be configured via environment variables in `docker-compose.yml`:

**MCP Server:**
- `MCP_HOST`: Bind address (default: `0.0.0.0` for remote access)
- `MCP_PORT`: Port number (default: `8000`)
- `PYTHONUNBUFFERED`: Set to `1` for real-time logs

**Web Interface:**
- `PORT`: Web server port (default: `5000`)
- `PYTHONUNBUFFERED`: Set to `1` for real-time logs

### Volume Mounts

Both services share the same data directory:
```yaml
volumes:
  - ./data:/app/data  # Notes stored here
```

All notes are stored in the local `./data/` directory for easy access and backup.

## Usage

### Accessing Services

**Web Interface:**
```
http://localhost:5000
```

**MCP Server HTTP API:**
```
http://localhost:8000
```

### Connecting MCP Clients

Configure your MCP client to connect to:
```
http://localhost:8000
```

Or for remote access (replace with your server IP):
```
http://YOUR_SERVER_IP:8000
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mcp-server
docker compose logs -f web-interface
```

### Stopping Services

```bash
# Stop but keep containers
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything including volumes
docker compose down -v
```

## Remote Access

To access the services from other machines:

1. **Update firewall rules** to allow ports 5000 and 8000
2. **Access services using server IP:**
   - Web: `http://YOUR_SERVER_IP:5000`
   - MCP: `http://YOUR_SERVER_IP:8000`

### Security Considerations

⚠️ **Important:** This setup is for development/internal use. For production:

1. Use HTTPS with reverse proxy (nginx/traefik)
2. Add authentication (OAuth, API keys)
3. Enable rate limiting
4. Use Docker secrets for sensitive data
5. Run containers as non-root user
6. Keep containers updated

## Data Persistence

All notes are stored in `./data/` directory:

```
./data/
  ├── <project1>/
  │   ├── <note1>_<timestamp>.md
  │   └── <note2>_<timestamp>.md
  ├── <project2>/
  │   └── <note3>_<timestamp>.md
  └── search_index.json
```

### Backup

Simply backup the `./data/` directory:

```bash
# Create backup
tar -czf notes-backup-$(date +%Y%m%d).tar.gz ./data

# Restore backup
tar -xzf notes-backup-20251005.tar.gz
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Port already in use

```bash
# Find process using port 5000
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Cannot connect remotely

1. Check firewall: `sudo ufw allow 8000` (Linux)
2. Verify service is listening: `docker compose ps`
3. Check container logs: `docker compose logs mcp-server`
4. Test locally first: `curl http://localhost:8000`

### Templates not created

```bash
# Rebuild with templates
docker compose down
docker compose build
docker compose up -d
```

### Data not persisting

Check volume mount in `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data  # Must be present
```

## Health Checks

The web interface includes a health check that runs every 30 seconds:

```bash
# Check health status
docker compose ps

# Should show "healthy" status for web-interface
```

## Updates

To update the application:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

## Development

For development with live code reloading, mount the source directory:

```yaml
volumes:
  - ./data:/app/data
  - ./src:/app/src  # Add this for live reload
```

Then restart containers after code changes:
```bash
docker compose restart
```
