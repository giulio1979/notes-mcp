"""Main MCP server for notes management."""

import asyncio
import argparse
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession
from mcp.server.fastmcp import Context

from .storage import NotesStorage
from .search import NotesSearcher


# Initialize FastMCP server
mcp = FastMCP(
    "Notes Manager",
    instructions=(
        "A server for managing versioned notes organized by projects (best practice, a project is a GIT repository name). "
        "Notes are automatically versioned with timestamps and can be searched using fuzzy matching."
    ),
)

# Initialize storage and search
storage = NotesStorage()
searcher = NotesSearcher(storage)


@mcp.tool()
async def store_note(project: str, title: str, content: str) -> str:
    """Store a new note or update an existing one.
    
    Notes are automatically versioned with timestamps. Each save creates a new version.
    
    Args:
        project: Project or topic name to organize the note
        title: Title of the note
        content: Content of the note in markdown format
        
    Returns:
        Success message with the file path where the note was stored
    """
    try:
        filepath = await storage.store_note(project, title, content)
        # Update search index for this project
        await searcher.rebuild_index()
        return f"Note stored successfully at: {filepath}"
    except Exception as e:
        return f"Error storing note: {str(e)}"


@mcp.tool()
async def retrieve_note(project: str, title: str, version: str = None) -> str:
    """Retrieve a note by project and title.
    
    By default, retrieves the latest version. Optionally specify a version timestamp.
    
    Args:
        project: Project or topic name
        title: Title of the note
        version: Optional version timestamp (ISO format) to retrieve a specific version
        
    Returns:
        The note content with metadata
    """
    try:
        content, timestamp = await storage.retrieve_note(project, title, version)
        return f"# {title}\n\n**Project:** {project}\n**Version:** {timestamp}\n\n---\n\n{content}"
    except FileNotFoundError as e:
        return f"Note not found: {str(e)}"
    except Exception as e:
        return f"Error retrieving note: {str(e)}"


@mcp.tool()
def list_projects() -> str:
    """List all available projects.
    
    Returns:
        A formatted list of all project names
    """
    try:
        projects = storage.list_projects()
        if not projects:
            return "No projects found."
        
        return "Available projects:\n" + "\n".join(f"- {p}" for p in projects)
    except Exception as e:
        return f"Error listing projects: {str(e)}"


@mcp.tool()
def list_notes(project: str) -> str:
    """List all notes in a project.
    
    Shows each note's title and its latest version timestamp.
    
    Args:
        project: Project or topic name
        
    Returns:
        A formatted list of notes with their latest versions
    """
    try:
        notes = storage.list_notes(project)
        if not notes:
            return f"No notes found in project '{project}'."
        
        result = f"Notes in project '{project}':\n"
        for note in notes:
            result += f"- {note['title']} (latest: {note['latest_version']})\n"
        
        return result
    except Exception as e:
        return f"Error listing notes: {str(e)}"


@mcp.tool()
async def search_notes(query: str, project: str = None) -> str:
    """Search for notes using fuzzy matching.
    
    Searches across note titles and content. Optionally limit to a specific project.
    
    Args:
        query: Search query text
        project: Optional project name to limit search scope
        
    Returns:
        A formatted list of matching notes with excerpts and relevance scores
    """
    try:
        # Ensure index is built
        if not searcher.index:
            await searcher.rebuild_index()
        
        results = searcher.search(query, project)
        
        if not results:
            scope = f"in project '{project}'" if project else "across all projects"
            return f"No results found for '{query}' {scope}."
        
        output = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results[:10], 1):  # Limit to top 10
            output += f"{i}. **{result.title}** (Project: {result.project})\n"
            output += f"   Score: {result.score:.1f}%\n"
            output += f"   {result.excerpt}\n\n"
        
        if len(results) > 10:
            output += f"... and {len(results) - 10} more results"
        
        return output
    except Exception as e:
        return f"Error searching notes: {str(e)}"


@mcp.tool()
async def rebuild_index() -> str:
    """Rebuild the search index for all notes.
    
    This scans all notes across all projects and rebuilds the search index.
    Useful after importing notes or if search results seem outdated.
    
    Returns:
        Success message with the number of notes indexed
    """
    try:
        count = await searcher.rebuild_index()
        return f"Search index rebuilt successfully. Indexed {count} notes."
    except Exception as e:
        return f"Error rebuilding index: {str(e)}"


@mcp.tool()
async def delete_note(project: str, title: str, version: str = None) -> str:
    """Delete a note or a specific version of a note.
    
    Use this to remove notes that are no longer needed, have been consolidated,
    or are outdated. Useful for agentic workflows like summarizing multiple notes
    into one and cleaning up the originals.
    
    Args:
        project: Project or topic name
        title: Note title
        version: Optional version timestamp (ISO format). If not provided, deletes ALL versions of the note.
        
    Returns:
        Success message with count of deleted files
        
    Examples:
        - delete_note("Python Learning", "Old Draft") -> Deletes all versions
        - delete_note("Python Learning", "AsyncIO", "2024-10-04T12:00:00") -> Deletes specific version
        
    Warning:
        Without a version parameter, this will delete ALL versions of the note!
    """
    try:
        result = await storage.delete_note(project, title, version)
        
        # Update search index after deletion
        await searcher.rebuild_index()
        
        if result["deleted"] == 1:
            return f"Successfully deleted 1 file: {result['files'][0]}"
        else:
            files_list = "\n".join(f"  - {f}" for f in result["files"])
            return f"Successfully deleted {result['deleted']} files:\n{files_list}"
            
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error deleting note: {str(e)}"


@mcp.tool()
def get_deep_link(
    project: str, 
    title: str = None, 
    version: str = None,
    web_server_url: str = "http://localhost:5000"
) -> str:
    """Generate a deep link to a project or note in the web interface.
    
    Creates a shareable URL that directly links to a specific project's notes list
    or to a specific note. This is useful for sharing references to notes with others.
    
    Args:
        project: Project or topic name
        title: Optional note title (if not provided, links to project view)
        version: Optional version timestamp for a specific note version
        web_server_url: Base URL of the web server (default: http://localhost:5000)
        
    Returns:
        Deep link URL that can be shared
        
    Examples:
        - get_deep_link("Python Learning") -> Links to all Python Learning notes
        - get_deep_link("Python Learning", "AsyncIO Basics") -> Links to specific note
        - get_deep_link("Python Learning", "AsyncIO Basics", "2024-10-04T12:00:00") -> Links to specific version
    """
    try:
        from urllib.parse import quote
        
        # Clean up the base URL
        web_server_url = web_server_url.rstrip('/')
        
        if title:
            # Link to specific note
            link = f"{web_server_url}/note/{quote(project)}/{quote(title)}"
            if version:
                link += f"?version={quote(version)}"
            
            version_info = f" (version: {version})" if version else ""
            return f"Deep link to note '{title}' in project '{project}'{version_info}:\n{link}"
        else:
            # Link to project view
            link = f"{web_server_url}/project/{quote(project)}"
            return f"Deep link to project '{project}':\n{link}"
            
    except Exception as e:
        return f"Error generating deep link: {str(e)}"


def main():
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Notes MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", 8000)),
        help="Port for HTTP transport (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("MCP_HOST", "localhost"),
        help="Host for HTTP transport (default: localhost)",
    )
    
    args = parser.parse_args()
    
    # Build the search index on startup
    asyncio.run(searcher.rebuild_index())
    
    # Run the server with specified transport
    if args.transport == "streamable-http":
        # For HTTP transport, use FastMCP's built-in HTTP app
        import uvicorn
        app = mcp.streamable_http_app()
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # For stdio, use the standard run method
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
