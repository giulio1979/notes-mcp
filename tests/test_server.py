"""Tests for the MCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.server import (
    store_note,
    retrieve_note,
    list_projects,
    list_notes,
    search_notes,
    rebuild_index,
)


@pytest.mark.asyncio
async def test_store_note_success():
    """Test successful note storage."""
    with patch("src.server.storage") as mock_storage, \
         patch("src.server.searcher") as mock_searcher:
        
        mock_storage.store_note = AsyncMock(return_value="/path/to/note.md")
        mock_searcher.rebuild_index = AsyncMock(return_value=1)
        
        result = await store_note("Test Project", "Test Note", "Test Content")
        
        assert "successfully" in result
        assert "/path/to/note.md" in result
        mock_storage.store_note.assert_called_once_with("Test Project", "Test Note", "Test Content")


@pytest.mark.asyncio
async def test_store_note_error():
    """Test note storage with error."""
    with patch("src.server.storage") as mock_storage, \
         patch("src.server.searcher") as mock_searcher:
        
        mock_storage.store_note = AsyncMock(side_effect=Exception("Storage error"))
        mock_searcher.rebuild_index = AsyncMock()
        
        result = await store_note("Test Project", "Test Note", "Test Content")
        
        assert "Error" in result


@pytest.mark.asyncio
async def test_retrieve_note_success():
    """Test successful note retrieval."""
    with patch("src.server.storage") as mock_storage:
        mock_storage.retrieve_note = AsyncMock(
            return_value=("Note content", "2024-01-01T12:00:00")
        )
        
        result = await retrieve_note("Test Project", "Test Note")
        
        assert "Test Note" in result
        assert "Note content" in result
        assert "2024-01-01T12:00:00" in result


@pytest.mark.asyncio
async def test_retrieve_note_not_found():
    """Test retrieving non-existent note."""
    with patch("src.server.storage") as mock_storage:
        mock_storage.retrieve_note = AsyncMock(
            side_effect=FileNotFoundError("Note not found")
        )
        
        result = await retrieve_note("Test Project", "Nonexistent Note")
        
        assert "not found" in result


def test_list_projects_success():
    """Test listing projects."""
    with patch("src.server.storage") as mock_storage:
        mock_storage.list_projects = MagicMock(return_value=["Project 1", "Project 2"])
        
        result = list_projects()
        
        assert "Project 1" in result
        assert "Project 2" in result


def test_list_projects_empty():
    """Test listing projects when none exist."""
    with patch("src.server.storage") as mock_storage:
        mock_storage.list_projects = MagicMock(return_value=[])
        
        result = list_projects()
        
        assert "No projects found" in result


def test_list_notes_success():
    """Test listing notes in a project."""
    with patch("src.server.storage") as mock_storage:
        mock_storage.list_notes = MagicMock(return_value=[
            {"title": "Note 1", "latest_version": "2024-01-01T12:00:00"},
            {"title": "Note 2", "latest_version": "2024-01-02T12:00:00"},
        ])
        
        result = list_notes("Test Project")
        
        assert "Note 1" in result
        assert "Note 2" in result


@pytest.mark.asyncio
async def test_search_notes_success():
    """Test successful note search."""
    with patch("src.server.searcher") as mock_searcher:
        from src.search import SearchResult
        
        mock_searcher.index = {"Project": {}}  # Non-empty index
        mock_searcher.search = MagicMock(return_value=[
            SearchResult(
                project="Test Project",
                title="Test Note",
                content="Test content",
                score=85.5,
                excerpt="...Test content..."
            )
        ])
        
        result = await search_notes("test query")
        
        assert "Test Note" in result
        assert "Test Project" in result


@pytest.mark.asyncio
async def test_search_notes_no_results():
    """Test search with no results."""
    with patch("src.server.searcher") as mock_searcher:
        mock_searcher.index = {"Project": {}}  # Non-empty index
        mock_searcher.search = MagicMock(return_value=[])
        
        result = await search_notes("nonexistent query")
        
        assert "No results found" in result


@pytest.mark.asyncio
async def test_rebuild_index_success():
    """Test rebuilding search index."""
    with patch("src.server.searcher") as mock_searcher:
        mock_searcher.rebuild_index = AsyncMock(return_value=42)
        
        result = await rebuild_index()
        
        assert "successfully" in result
        assert "42" in result
