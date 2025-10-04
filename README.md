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
docker-compose up -d

# Access web interface at http://localhost:5000
# MCP server available at http://localhost:8000/mcp
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment guide.

### Option 2: Local Installation

```bash
# Install dependencies using uv
uv sync

# Or using pip
pip install -e .
```

## Usage

### Running the MCP Server

```bash
# Using stdio transport (default)
uv run python -m src.server

# Using SSE transport
uv run python -m src.server --transport sse --port 8000
```

### Running the Web Interface

```bash
uv run python -m src.web_server
```

The web interface will be available at `http://localhost:5000`

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

### 7. `get_deep_link`
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
