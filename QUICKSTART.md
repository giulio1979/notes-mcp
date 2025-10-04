# Quick Start Guide

## Installation

1. **Clone or download the project**
   ```bash
   cd d:\Nextcloud\BackupWork\CURRENT\notes-mcp
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   # Or install specific packages:
   pip install mcp>=1.16.0 python-dateutil aiofiles rapidfuzz flask markdown
   ```

3. **Install dev dependencies (optional)**
   ```bash
   pip install pytest pytest-asyncio pytest-cov black ruff
   ```

## Running the MCP Server

### Option 1: stdio Transport (Default - for MCP clients)
```bash
python -m src.server
```

This runs the server using standard input/output, which is the standard way MCP servers communicate with clients like Claude Desktop or other MCP-compatible applications.

### Option 2: SSE Transport (Server-Sent Events)
```bash
python -m src.server --transport sse --port 8000
```

Access at: `http://localhost:8000/sse`

### Option 3: Streamable HTTP Transport
```bash
python -m src.server --transport streamable-http --port 8000
```

Access at: `http://localhost:8000/mcp`

## Running the Web Interface

```bash
python -m src.web_server
```

Then open your browser to: `http://localhost:5000`

## Configuring with Claude Desktop (or other MCP clients)

Add this to your MCP client configuration (usually `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "notes-mcp": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "d:/Nextcloud/BackupWork/CURRENT/notes-mcp"
    }
  }
}
```

**Windows Path Example:**
```json
{
  "mcpServers": {
    "notes-mcp": {
      "command": "D:/Nextcloud/BackupWork/CURRENT/notes-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "d:/Nextcloud/BackupWork/CURRENT/notes-mcp"
    }
  }
}
```

## Using the Server

### Available Tools

1. **store_note** - Store or update a note
   ```json
   {
     "project": "Python Learning",
     "title": "AsyncIO Basics",
     "content": "# AsyncIO Basics\\n\\nContent here..."
   }
   ```

2. **retrieve_note** - Get a note
   ```json
   {
     "project": "Python Learning",
     "title": "AsyncIO Basics",
     "version": "2024-10-04T12:00:00"  // optional
   }
   ```

3. **list_projects** - List all projects
   ```json
   {}
   ```

4. **list_notes** - List notes in a project
   ```json
   {
     "project": "Python Learning"
   }
   ```

5. **search_notes** - Search for notes
   ```json
   {
     "query": "async programming",
     "project": "Python Learning"  // optional
   }
   ```

6. **rebuild_index** - Rebuild search index
   ```json
   {}
   ```

## Example Usage

Once configured, you can ask your MCP client (like Claude):

- "Store a note about Python decorators in my Python Learning project"
- "Show me my notes about async programming"
- "List all my projects"
- "Search for notes about Docker"
- "Retrieve the latest version of my AsyncIO Basics note"

## Data Storage

Notes are stored in the `data/` directory:
```
data/
├── Python_Learning/
│   ├── AsyncIO_Basics_2024-10-04T12-00-00.md
│   └── Type_Hints_2024-10-04T12-05-00.md
└── DevOps/
    └── Docker_Basics_2024-10-04T13-00-00.md
```

Each note is versioned with a timestamp, allowing you to keep a history of changes.

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_storage.py -v
```

## Troubleshooting

### Server won't start
- Ensure Python 3.10+ is installed
- Check that all dependencies are installed: `pip install -e .`
- Verify the virtual environment is activated

### Notes not found
- Check the `data/` directory exists
- Verify project and note names match (case-sensitive)
- Try rebuilding the search index: call the `rebuild_index` tool

### Web interface shows no notes
- Make sure you've created some notes first using the MCP server
- Try accessing: `http://localhost:5000/rebuild_index`
- Check that the web server is running: `python -m src.web_server`

## Development

### Code formatting
```bash
black src tests
```

### Linting
```bash
ruff check src tests
```

### Adding new features
1. Add implementation in `src/`
2. Add tests in `tests/`
3. Run tests: `pytest`
4. Update README.md with new features

## Next Steps

- Integrate with your favorite MCP client (Claude Desktop, Continue.dev, etc.)
- Create notes for your projects
- Use the web interface to browse and search
- Set up automated backups of the `data/` directory
