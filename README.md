# Notes MCP Server

A Model Context Protocol (MCP) server for managing versioned notes organized by projects/topics.

## Features

- **Store Notes**: Create and save notes for different projects/topics
- **Retrieve Notes**: Get the latest version of notes or specific versions
- **Version Control**: Automatic versioning of notes with timestamps
- **Search**: Fuzzy search across all notes
- **Web Interface**: Browse notes through a web interface
- **Project Organization**: Notes are organized in project-specific folders
- **Deep Links**: Generate shareable URLs to specific projects or notes

## Installation

### Option 1: Docker (Recommended)

```bash
# Start both MCP server and web interface
docker compose up -d

# Access web interface at http://localhost:5000
# MCP server HTTP API at http://localhost:8000
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment guide.

### Option 2: Local Installation

```bash
# Install dependencies using pip
pip install -e .

# Or install from pyproject.toml
pip install mcp python-dateutil aiofiles rapidfuzz flask markdown uvicorn
```

## Usage

### Running the MCP Server

```bash
# Using stdio transport (default, for local MCP clients)
python -m src.server

# Using HTTP transport (for remote access)
python -m src.server --transport streamable-http --host 0.0.0.0 --port 8000
```

### Running the Web Interface

```bash
python -m src.web_server
```

The web interface will be available at `http://localhost:5000`

### Transports

The MCP server supports two transport modes:

1. **stdio** (default): For local MCP clients that communicate via standard input/output
   ```bash
   python -m src.server
   ```

2. **streamable-http**: For remote access via HTTP API
   ```bash
   python -m src.server --transport streamable-http --host 0.0.0.0 --port 8000
   ```
   Access at: `http://localhost:8000`

## MCP Tools

### 1. `store_note`
Store a new note or update an existing one.

**Parameters:**
- `project` (string): Project/topic name
- `title` (string): Note title
- `content` (string): Note content

**Returns:** Success message with file path

### 2. `retrieve_note`
Retrieve a note by project and title.

**Parameters:**
- `project` (string): Project/topic name
- `title` (string): Note title
- `version` (string, optional): Specific version timestamp (defaults to latest)

**Returns:** Note content

### 3. `list_projects`
List all available projects.

**Returns:** List of project names

### 4. `list_notes`
List all notes in a project.

**Parameters:**
- `project` (string): Project/topic name

**Returns:** List of note titles with their latest versions

### 5. `search_notes`
Search for notes using fuzzy matching.

**Parameters:**
- `query` (string): Search query
- `project` (string, optional): Limit search to specific project

**Returns:** List of matching notes with excerpts

### 6. `rebuild_index`
Rebuild the search index for all notes.

**Returns:** Success message with count of indexed notes

### 7. `delete_note`
Delete a note or specific version of a note. ⚠️ **New in v1.1**

**Parameters:**
- `project` (string): Project/topic name
- `title` (string): Note title
- `version` (string, optional): Specific version timestamp. If omitted, deletes ALL versions

**Returns:** Success message with count of deleted files

**Use Cases:**
- Consolidate multiple notes into one summary, then delete originals
- Remove outdated or duplicate notes
- Clean up old versions
- Agentic workflows for note management

**Warning:** Without the `version` parameter, this deletes ALL versions of the note!

### 8. `get_deep_link`
Generate a shareable deep link to a project or note.

**Parameters:**
- `project` (string): Project/topic name
- `title` (string, optional): Note title (if omitted, links to project view)
- `version` (string, optional): Specific version timestamp
- `web_server_url` (string, optional): Base URL of web server (default: http://localhost:5000)

**Returns:** Shareable URL that directly links to the project or note

## Architecture

```
notes-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── storage.py         # File storage and versioning
│   ├── search.py          # Search and indexing
│   └── web_server.py      # Web interface
├── tests/
│   ├── __init__.py
│   ├── test_storage.py
│   ├── test_search.py
│   └── test_server.py
├── data/                  # Notes storage directory
│   └── {project}/         # Project-specific folders
│       └── {title}_{timestamp}.md
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Multi-container setup
├── .dockerignore          # Docker build exclusions
└── pyproject.toml
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_storage.py
```

### Code Formatting

```bash
# Format code with black
uv run black src tests

# Lint with ruff
uv run ruff check src tests
```

## License

MIT
