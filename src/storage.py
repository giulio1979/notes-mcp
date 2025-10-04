"""Storage module for managing versioned notes."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiofiles
import asyncio


class NotesStorage:
    """Handles storage and versioning of notes."""

    def __init__(self, base_dir: str = "data"):
        """Initialize the storage manager.
        
        Args:
            base_dir: Base directory for storing notes
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def _get_project_dir(self, project: str) -> Path:
        """Get the directory for a project.
        
        Args:
            project: Project name
            
        Returns:
            Path to project directory
        """
        # Sanitize project name for filesystem
        safe_project = "".join(c for c in project if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_project = safe_project.replace(" ", "_")
        project_dir = self.base_dir / safe_project
        project_dir.mkdir(exist_ok=True)
        return project_dir

    def _generate_filename(self, title: str, timestamp: Optional[str] = None) -> str:
        """Generate a filename for a note.
        
        Args:
            title: Note title
            timestamp: Optional timestamp string (ISO format)
            
        Returns:
            Filename with timestamp
        """
        # Sanitize title for filesystem
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_title = safe_title.replace(" ", "_")
        
        if timestamp is None:
            timestamp = datetime.now().isoformat().replace(":", "-")
        else:
            # Ensure timestamp is filesystem-safe
            timestamp = timestamp.replace(":", "-")
        
        return f"{safe_title}_{timestamp}.md"

    async def store_note(self, project: str, title: str, content: str) -> str:
        """Store a new version of a note.
        
        Args:
            project: Project name
            title: Note title
            content: Note content
            
        Returns:
            Path to the stored note file
        """
        project_dir = self._get_project_dir(project)
        filename = self._generate_filename(title)
        filepath = project_dir / filename
        
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return str(filepath)

    async def retrieve_note(
        self, project: str, title: str, version: Optional[str] = None
    ) -> tuple[str, str]:
        """Retrieve a note by project and title.
        
        Args:
            project: Project name
            title: Note title
            version: Optional version timestamp (ISO format)
            
        Returns:
            Tuple of (content, version_timestamp)
            
        Raises:
            FileNotFoundError: If note not found
        """
        project_dir = self._get_project_dir(project)
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_title = safe_title.replace(" ", "_")
        
        # Find all versions of this note
        pattern = f"{safe_title}_*.md"
        versions = sorted(project_dir.glob(pattern), reverse=True)
        
        if not versions:
            raise FileNotFoundError(f"Note '{title}' not found in project '{project}'")
        
        # If specific version requested, find it
        if version:
            version_safe = version.replace(":", "-")
            target_file = None
            for v in versions:
                if version_safe in v.name:
                    target_file = v
                    break
            if not target_file:
                raise FileNotFoundError(
                    f"Version '{version}' of note '{title}' not found in project '{project}'"
                )
        else:
            # Get latest version
            target_file = versions[0]
        
        # Read the note content
        async with aiofiles.open(target_file, "r", encoding="utf-8") as f:
            content = await f.read()
        
        # Extract timestamp from filename
        timestamp = target_file.stem.split("_")[-1].replace("-", ":")
        
        return content, timestamp

    def list_projects(self) -> list[str]:
        """List all projects.
        
        Returns:
            List of project names
        """
        projects = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                projects.append(item.name.replace("_", " "))
        return sorted(projects)

    def list_notes(self, project: str) -> list[dict[str, str]]:
        """List all notes in a project with their latest versions.
        
        Args:
            project: Project name
            
        Returns:
            List of dictionaries with 'title' and 'latest_version' keys
        """
        project_dir = self._get_project_dir(project)
        
        # Group notes by title
        notes_map = {}
        for filepath in project_dir.glob("*.md"):
            # Extract title (everything before the last underscore and timestamp)
            parts = filepath.stem.rsplit("_", 1)
            if len(parts) == 2:
                title, timestamp = parts
                title = title.replace("_", " ")
                timestamp = timestamp.replace("-", ":")
                
                if title not in notes_map or timestamp > notes_map[title]:
                    notes_map[title] = timestamp
        
        # Convert to list of dictionaries
        notes = [
            {"title": title, "latest_version": version}
            for title, version in sorted(notes_map.items())
        ]
        
        return notes

    def get_all_notes(self) -> list[dict[str, str]]:
        """Get all notes across all projects.
        
        Returns:
            List of dictionaries with 'project', 'title', 'path', and 'timestamp' keys
        """
        all_notes = []
        
        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            project = project_dir.name.replace("_", " ")
            
            for filepath in project_dir.glob("*.md"):
                parts = filepath.stem.rsplit("_", 1)
                if len(parts) == 2:
                    title, timestamp = parts
                    title = title.replace("_", " ")
                    timestamp = timestamp.replace("-", ":")
                    
                    all_notes.append({
                        "project": project,
                        "title": title,
                        "path": str(filepath),
                        "timestamp": timestamp,
                    })
        
        return all_notes

    async def read_note_content(self, filepath: str) -> str:
        """Read content of a note file.
        
        Args:
            filepath: Path to note file
            
        Returns:
            Note content
        """
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            return await f.read()
