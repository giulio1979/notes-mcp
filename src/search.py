"""Search and indexing module for notes."""

from typing import Optional
from rapidfuzz import fuzz, process
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a search result."""
    project: str
    title: str
    content: str
    score: float
    excerpt: str


class NotesSearcher:
    """Handles searching and indexing of notes."""

    def __init__(self, storage):
        """Initialize the searcher.
        
        Args:
            storage: NotesStorage instance
        """
        self.storage = storage
        self.index = {}  # project -> {title -> content}

    async def rebuild_index(self) -> int:
        """Rebuild the search index from all notes.
        
        Returns:
            Number of notes indexed
        """
        self.index = {}
        notes = self.storage.get_all_notes()
        
        # Group by project and title, keeping only latest versions
        latest_notes = {}
        for note in notes:
            key = (note["project"], note["title"])
            if key not in latest_notes or note["timestamp"] > latest_notes[key]["timestamp"]:
                latest_notes[key] = note
        
        # Read content and build index
        count = 0
        for (project, title), note in latest_notes.items():
            content = await self.storage.read_note_content(note["path"])
            
            if project not in self.index:
                self.index[project] = {}
            
            self.index[project][title] = {
                "content": content,
                "timestamp": note["timestamp"],
                "path": note["path"],
            }
            count += 1
        
        return count

    def search(
        self, query: str, project: Optional[str] = None, threshold: int = 60
    ) -> list[SearchResult]:
        """Search for notes using fuzzy matching.
        
        Args:
            query: Search query
            project: Optional project to limit search
            threshold: Minimum similarity score (0-100)
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        results = []
        
        # Determine which projects to search
        projects_to_search = [project] if project else list(self.index.keys())
        
        for proj in projects_to_search:
            if proj not in self.index:
                continue
            
            for title, note_data in self.index[proj].items():
                content = note_data["content"]
                
                # Calculate scores for different fields
                title_score = fuzz.partial_ratio(query.lower(), title.lower())
                content_score = fuzz.partial_ratio(query.lower(), content.lower())
                
                # Use the best score
                best_score = max(title_score, content_score)
                
                if best_score >= threshold:
                    # Generate excerpt
                    excerpt = self._generate_excerpt(content, query)
                    
                    results.append(
                        SearchResult(
                            project=proj,
                            title=title,
                            content=content,
                            score=best_score,
                            excerpt=excerpt,
                        )
                    )
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results

    def _generate_excerpt(self, content: str, query: str, context_chars: int = 150) -> str:
        """Generate an excerpt around the query match.
        
        Args:
            content: Full content
            query: Search query
            context_chars: Characters of context around match
            
        Returns:
            Excerpt string
        """
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find the best match position
        pos = content_lower.find(query_lower)
        
        if pos == -1:
            # If exact match not found, just return beginning
            return content[:context_chars * 2] + ("..." if len(content) > context_chars * 2 else "")
        
        # Calculate excerpt bounds
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)
        
        # Extract excerpt
        excerpt = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."
        
        return excerpt
