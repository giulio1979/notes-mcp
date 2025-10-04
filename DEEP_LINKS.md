# Deep Links Feature

The Notes MCP Server includes a powerful deep linking feature that allows you to create shareable URLs that directly link to specific projects or notes.

## What are Deep Links?

Deep links are permanent URLs that point directly to:
- A project's notes list
- A specific note
- A specific version of a note

These links can be shared with others to provide direct access to your notes through the web interface.

## Features

### 1. Web Interface Integration

When viewing a project or note in the web interface, you'll see a "Share this project" or "Share this note" section with:
- A readonly text field containing the deep link
- A "Copy Link" button for easy copying
- Visual feedback when the link is copied

### 2. MCP Tool: `get_deep_link`

Generate deep links programmatically using the MCP server tool.

#### Examples

**Link to a project:**
```json
{
  "tool": "get_deep_link",
  "arguments": {
    "project": "Python Learning"
  }
}
```
Returns: `http://localhost:5000/project/Python%20Learning`

**Link to a specific note:**
```json
{
  "tool": "get_deep_link",
  "arguments": {
    "project": "Python Learning",
    "title": "AsyncIO Basics"
  }
}
```
Returns: `http://localhost:5000/note/Python%20Learning/AsyncIO%20Basics`

**Link to a specific version:**
```json
{
  "tool": "get_deep_link",
  "arguments": {
    "project": "Python Learning",
    "title": "AsyncIO Basics",
    "version": "2024-10-04T12:00:00"
  }
}
```
Returns: `http://localhost:5000/note/Python%20Learning/AsyncIO%20Basics?version=2024-10-04T12%3A00%3A00`

**Custom web server URL:**
```json
{
  "tool": "get_deep_link",
  "arguments": {
    "project": "Python Learning",
    "web_server_url": "https://notes.mycompany.com"
  }
}
```
Returns: `https://notes.mycompany.com/project/Python%20Learning`

### 3. REST API Endpoints

The web server also provides REST API endpoints for generating deep links:

**Get project deep link:**
```bash
GET /api/deep-link/project/<project_name>
```

Response:
```json
{
  "project": "Python Learning",
  "deep_link": "http://localhost:5000/project/Python%20Learning",
  "url": "http://localhost:5000/project/Python%20Learning"
}
```

**Get note deep link:**
```bash
GET /api/deep-link/note/<project_name>/<title>?version=<optional_version>
```

Response:
```json
{
  "project": "Python Learning",
  "title": "AsyncIO Basics",
  "version": null,
  "deep_link": "http://localhost:5000/note/Python%20Learning/AsyncIO%20Basics",
  "url": "http://localhost:5000/note/Python%20Learning/AsyncIO%20Basics"
}
```

## URL Encoding

All special characters in project names and note titles are automatically URL-encoded:
- Spaces → `%20`
- Slashes → `%2F`
- Colons → `%3A`
- Question marks → `%3F`
- etc.

This ensures the links work correctly even with special characters in names.

## Use Cases

### 1. Sharing with Team Members
```
"Hey, check out my notes on Docker: http://localhost:5000/project/DevOps"
```

### 2. Documentation References
Include deep links in documentation to reference specific notes:
```markdown
For more details, see our [AsyncIO guide](http://notes.example.com/note/Python%20Learning/AsyncIO%20Basics)
```

### 3. Bookmarking
Save deep links in your browser bookmarks for quick access to frequently used notes.

### 4. Integration with Other Tools
Use the API endpoints or MCP tool to integrate deep links into:
- Slack/Teams messages
- Email notifications
- Project management tools
- CI/CD pipelines
- Custom dashboards

## Implementation Details

### Web Interface
- Deep links are automatically generated for each project and note view
- One-click copy functionality with visual feedback
- Links persist as long as the notes exist

### MCP Tool
- Synchronous function (no async/await needed)
- Validates inputs and handles errors gracefully
- Supports custom web server URLs for different environments

### REST API
- JSON responses with structured data
- URL-encoded paths for maximum compatibility
- No authentication required (suitable for internal networks)

## Configuration

### Default Web Server URL
The default is `http://localhost:5000`, but you can customize it:

**In MCP tool calls:**
```json
{
  "web_server_url": "https://notes.mycompany.com"
}
```

**For production deployments:**
Update the web server configuration or use environment variables:
```bash
export WEB_SERVER_BASE_URL="https://notes.mycompany.com"
```

## Examples in Different Contexts

### Claude Desktop Integration
```
User: "Generate a deep link for my Python Learning project"
Claude: *calls get_deep_link tool*
Claude: "Here's your deep link: http://localhost:5000/project/Python%20Learning
You can share this with your team to give them direct access to all notes in this project."
```

### Python Script
```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Generate deep link
        result = await session.call_tool(
            "get_deep_link",
            arguments={
                "project": "Python Learning",
                "title": "AsyncIO Basics"
            }
        )
        print(result.content[0].text)
```

### cURL API Call
```bash
# Get project deep link
curl http://localhost:5000/api/deep-link/project/Python%20Learning

# Get note deep link
curl http://localhost:5000/api/deep-link/note/Python%20Learning/AsyncIO%20Basics

# Get specific version deep link
curl "http://localhost:5000/api/deep-link/note/Python%20Learning/AsyncIO%20Basics?version=2024-10-04T12:00:00"
```

## Benefits

1. **Easy Sharing** - Share specific notes without navigating through multiple pages
2. **Permanent Links** - Links remain valid as long as the notes exist
3. **Version Support** - Link to specific versions for reference
4. **URL Safe** - Automatic encoding handles special characters
5. **No Auth Required** - Perfect for internal team collaboration
6. **Multiple Access Methods** - Web UI, MCP tool, or REST API

## Future Enhancements

Potential improvements for the deep link feature:
- QR code generation for mobile access
- Short URL support (optional URL shortener integration)
- Link analytics (track which notes are most accessed)
- Expiring links for sensitive information
- Custom link aliases
- Markdown link generation

## Troubleshooting

### Link doesn't work
- Verify the web server is running on the specified URL
- Check that the project/note still exists
- Ensure special characters are properly encoded

### Cannot copy link
- Try manually selecting and copying the text
- Check browser console for JavaScript errors
- Verify clipboard permissions

### API returns 404
- Check the project and note names match exactly (case-sensitive)
- Verify URL encoding for special characters
- Ensure the web server is running

## Security Considerations

**Note:** Deep links provide direct access to notes without authentication. Consider:
- Running the web server on a private network
- Using a reverse proxy with authentication for public access
- Implementing rate limiting for the API endpoints
- Regular backups of the `data/` directory

For more information, see the main [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md).
