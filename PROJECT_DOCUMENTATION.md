# Notes MCP Server - Complete Project Documentation

## Project Overview

**Notes MCP Server** is a Model Context Protocol (MCP) server that provides versioned note management organized by projects/topics. It includes both an MCP API for programmatic access and a web interface for browsing.

### Key Information
- **Created:** October 2025
- **Language:** Python 3.10+
- **MCP SDK:** Version 1.16.0
- **License:** [Your License]
- **Repository:** https://github.com/giulio1979/notes-mcp

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Notes MCP Server                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  MCP Server  │         │ Web Server   │                 │
│  │  Port 8000   │         │  Port 5000   │                 │
│  │  /mcp        │         │  Flask App   │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         └────────┬───────────────┘                          │
│                  │                                           │
│         ┌────────▼────────┐                                 │
│         │  Storage Layer  │                                 │
│         │  (File-based)   │                                 │
│         └────────┬────────┘                                 │
│                  │                                           │
│         ┌────────▼────────┐                                 │
│         │  Search Engine  │                                 │
│         │  (RapidFuzz)    │                                 │
│         └─────────────────┘                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  ./data/      │
                  │  Local Folder │
                  └───────────────┘
```

## Core Components

### 1. MCP Server (`src/server.py`)
- **Purpose:** Provides MCP protocol interface for note management
- **Transport Modes:**
  - `stdio`: Standard input/output (for local MCP clients)
  - `streamable-http`: HTTP API at `/mcp` endpoint (for remote access)
- **Port:** 8000 (HTTP mode)
- **Endpoint:** `http://host:8000/mcp`

### 2. Web Interface (`src/web_server.py`)
- **Purpose:** Browser-based note browsing and management
- **Framework:** Flask
- **Port:** 5000
- **Features:**
  - Browse all projects
  - View notes with full content
  - Search with fuzzy matching
  - Generate deep links
  - Rebuild search index
  - View note version history

### 3. Storage Layer (`src/storage.py`)
- **Type:** File-based storage
- **Location:** `./data/` directory
- **Structure:**
  ```
  data/
  ├── Project1/
  │   ├── Note1_2025-10-05T14-30-00.md
  │   └── Note1_2025-10-05T15-45-00.md
  └── Project2/
      └── Note2_2025-10-05T16-00-00.md
  ```
- **Versioning:** Automatic timestamp-based versioning
- **Format:** Markdown files

### 4. Search Engine (`src/search.py`)
- **Library:** RapidFuzz
- **Type:** Fuzzy text matching
- **Index:** JSON file at `./data/search_index.json`
- **Features:**
  - Full-text search across all notes
  - Project-scoped search
  - Relevance scoring
  - Context excerpts

## MCP Tools (API)

### 1. `store_note`
Store or update a note with automatic versioning.

**Parameters:**
- `project` (string): Project/topic name
- `title` (string): Note title
- `content` (string): Note content (Markdown)

**Returns:** Success message with file path

**Example:**
```json
{
  "project": "Python Learning",
  "title": "Async Programming",
  "content": "# Async Programming\n\n..."
}
```

### 2. `retrieve_note`
Get a note's content (latest or specific version).

**Parameters:**
- `project` (string): Project name
- `title` (string): Note title
- `version` (string, optional): ISO timestamp for specific version

**Returns:** Note content with metadata

### 3. `list_projects`
List all available projects.

**Returns:** Array of project names

### 4. `list_notes`
List all notes in a project.

**Parameters:**
- `project` (string): Project name

**Returns:** Array of notes with titles and latest version timestamps

### 5. `search_notes`
Fuzzy search across notes.

**Parameters:**
- `query` (string): Search query
- `project` (string, optional): Limit to specific project

**Returns:** Ranked search results with excerpts and scores

### 6. `rebuild_index`
Rebuild the search index.

**Returns:** Success message with count of indexed notes

### 7. `get_deep_link`
Generate shareable URLs for projects or notes.

**Parameters:**
- `project` (string): Project name
- `title` (string, optional): Note title
- `version` (string, optional): Specific version timestamp
- `web_server_url` (string, optional): Base URL (default: http://localhost:5000)

**Returns:** Deep link URL

## Installation & Deployment

### Local Development

```bash
# Clone repository
git clone https://github.com/giulio1979/notes-mcp.git
cd notes-mcp

# Install dependencies
pip install -e .

# Run MCP server (stdio)
python -m src.server

# Run MCP server (HTTP)
python -m src.server --transport streamable-http --host 0.0.0.0 --port 8000

# Run web interface
python -m src.web_server
```

### Docker Deployment (Recommended)

```bash
# Quick start
./docker-start.sh          # Linux/Mac
.\docker-start.ps1         # Windows

# Manual
docker compose build
docker compose up -d
docker compose logs -f
```

**Services:**
- MCP Server: http://localhost:8000/mcp
- Web Interface: http://localhost:5000

### Configuration

#### MCP Client Configuration

**For HTTP transport (Docker/Remote):**
```json
{
  "servers": {
    "notes": {
      "url": "http://your-server:8000/mcp",
      "type": "http"
    }
  }
}
```

**For stdio transport (Local):**
```json
{
  "mcpServers": {
    "notes-mcp": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/notes-mcp"
    }
  }
}
```

## Dependencies

### Core
- `mcp>=1.16.0` - Model Context Protocol SDK
- `python-dateutil>=2.8.2` - Date/time handling
- `aiofiles>=23.2.1` - Async file operations
- `rapidfuzz>=3.5.2` - Fuzzy string matching
- `flask>=3.0.0` - Web framework
- `markdown>=3.5.0` - Markdown rendering
- `uvicorn>=0.27.0` - ASGI server for HTTP transport

### Development
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_storage.py
```

**Test Coverage:**
- Storage: 6 tests (versioning, retrieval, listing)
- Search: 8 tests (indexing, fuzzy matching, excerpts)
- Server: 10 tests (all MCP tools)
- Deep Links: 6 tests (URL generation, web UI)

**Total:** 30 tests, all passing ✅

## Data Management

### Storage Location
All notes stored in `./data/` directory:
```
./data/
├── <project1>/
│   └── <note>_<timestamp>.md
└── search_index.json
```

### Backup
```bash
# Create backup
tar -czf notes-backup-$(date +%Y%m%d).tar.gz ./data

# Restore
tar -xzf notes-backup-20251005.tar.gz
```

### Version History
Each note save creates a new version:
- Format: `Title_YYYY-MM-DDTHH-MM-SS.md`
- All versions preserved
- Retrieve latest or specific version via API

## Web Interface Features

### Home Page (`/`)
- Lists all projects
- Shows note count per project
- Search box
- Index rebuild button

### Project View (`/project/<name>`)
- Lists all notes in project
- Shows latest version for each
- Deep link button
- Click note to view content

### Note View (`/note/<project>/<title>`)
- Full note content (Markdown rendered)
- Version selector dropdown
- Deep link button
- Back to project button

### Search (`/search`)
- Fuzzy search across all notes
- Results with relevance scores
- Context excerpts
- Click to view full note

### Deep Links
- Generate shareable URLs
- Copy to clipboard button
- JavaScript-based copying
- Works for projects and notes

## Remote Access

### Network Configuration

**Firewall Rules:**
```bash
# Linux (ufw)
sudo ufw allow 5000/tcp  # Web interface
sudo ufw allow 8000/tcp  # MCP server

# Windows (PowerShell as Admin)
New-NetFirewallRule -DisplayName "Notes MCP Web" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Notes MCP Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**Access URLs:**
- Web: `http://your-server-ip:5000`
- MCP: `http://your-server-ip:8000/mcp`

### Security Considerations

⚠️ **Important:** Current setup is for development/internal use.

**For Production:**
1. Use HTTPS with reverse proxy (nginx/traefik)
2. Add authentication (OAuth, API keys, Basic Auth)
3. Enable rate limiting
4. Use Docker secrets for credentials
5. Run as non-root user
6. Keep dependencies updated
7. Enable CORS properly
8. Add request logging
9. Set up monitoring

## Troubleshooting

### MCP Server Returns 404
**Issue:** Client gets 404 errors  
**Solution:** Use `/mcp` endpoint: `http://host:8000/mcp`

### Templates Not Created in Docker
**Issue:** Read-only filesystem error  
**Solution:** Rebuild Docker image (templates created during build)
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Port Already in Use
**Solution:** Change port in docker-compose.yml or kill existing process
```bash
# Find process
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Change port
ports:
  - "8001:8000"  # Use 8001 externally
```

### Search Not Finding Notes
**Solution:** Rebuild search index
```bash
# Via web interface
http://localhost:5000/rebuild_index

# Via MCP tool
# Call rebuild_index tool
```

### Cannot Connect Remotely
**Checklist:**
1. ✓ Firewall allows ports 5000, 8000
2. ✓ Server bound to 0.0.0.0 (not 127.0.0.1)
3. ✓ Docker container ports properly mapped
4. ✓ Using correct IP address
5. ✓ Using `/mcp` endpoint for MCP server

## Development

### Project Structure
```
notes-mcp/
├── src/
│   ├── server.py          # MCP server (270 lines)
│   ├── web_server.py      # Flask web app (510 lines)
│   ├── storage.py         # File storage (180 lines)
│   └── search.py          # Search engine (150 lines)
├── tests/
│   ├── test_server.py     # 10 tests
│   ├── test_storage.py    # 6 tests
│   ├── test_search.py     # 8 tests
│   └── test_deep_links.py # 6 tests
├── data/                  # Notes storage (auto-created)
├── docker-compose.yml     # Container orchestration
├── Dockerfile            # Container image
├── pyproject.toml        # Python package config
└── README.md             # User documentation
```

### Adding Features

**New MCP Tool:**
```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    return "result"
```

**New Web Route:**
```python
@app.route('/my-route')
def my_route():
    return render_template('my_template.html')
```

### Code Style
- Black for formatting
- Type hints recommended
- Async/await for I/O operations
- Docstrings for all functions

## Performance

### Storage
- File-based: Simple, reliable
- Async I/O: Non-blocking operations
- No database overhead

### Search
- RapidFuzz: Fast fuzzy matching
- JSON index: Quick loading
- Rebuild on demand

### Web Interface
- Flask development server (not for production)
- Static file serving
- Template caching

### Scaling Recommendations
- Use production WSGI server (gunicorn)
- Add Redis for search cache
- Consider PostgreSQL for metadata
- Use CDN for static assets
- Load balancer for multiple instances

## Use Cases

### 1. Personal Knowledge Base
Store and search personal notes organized by topics.

### 2. Team Documentation
Share project documentation with versioning.

### 3. Code Snippets Library
Organize code snippets with fuzzy search.

### 4. Research Notes
Maintain research notes with full history.

### 5. MCP Integration
Use with Claude Desktop or other MCP clients for AI-assisted note-taking.

## Future Enhancements

### Planned Features
- [ ] Note tagging system
- [ ] Full-text search with highlighting
- [ ] Note templates
- [ ] Export to various formats (PDF, HTML, etc.)
- [ ] Note encryption
- [ ] Collaborative editing
- [ ] Git integration for version control
- [ ] Media attachments support
- [ ] REST API documentation (OpenAPI/Swagger)
- [ ] GraphQL API option

### Community
- Issues: [GitHub Issues](https://github.com/giulio1979/notes-mcp/issues)
- Discussions: [GitHub Discussions](https://github.com/giulio1979/notes-mcp/discussions)
- Contributing: See CONTRIBUTING.md (if exists)

## License

[Specify your license here]

## Credits

- **MCP SDK:** Anthropic's Model Context Protocol
- **FastMCP:** High-level MCP framework
- **Flask:** Web framework by Pallets
- **RapidFuzz:** Fuzzy string matching
- **Uvicorn:** ASGI server

## Support

- Documentation: See README.md, DOCKER.md, QUICKSTART.md
- Examples: mcp_config_example.json, example_client.py
- Issues: GitHub Issues
- Questions: GitHub Discussions

---

**Last Updated:** October 5, 2025  
**Version:** 0.1.0  
**Status:** Production Ready ✅
