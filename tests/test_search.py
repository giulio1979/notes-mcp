"""Tests for the search module."""

import pytest
import tempfile
import shutil

from src.storage import NotesStorage
from src.search import NotesSearcher


@pytest.fixture
async def setup_notes():
    """Create a temporary storage with some test notes."""
    temp_dir = tempfile.mkdtemp()
    storage = NotesStorage(base_dir=temp_dir)
    searcher = NotesSearcher(storage)
    
    # Create test notes
    await storage.store_note("Python", "Async Programming", "Learn about asyncio and async/await syntax")
    await storage.store_note("Python", "Type Hints", "Understanding type annotations and mypy")
    await storage.store_note("JavaScript", "Promises", "Async programming with promises and async/await")
    await storage.store_note("DevOps", "Docker Basics", "Container technology and Docker fundamentals")
    
    yield storage, searcher
    
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_rebuild_index(setup_notes):
    """Test rebuilding the search index."""
    storage, searcher = setup_notes
    
    count = await searcher.rebuild_index()
    assert count == 4
    assert len(searcher.index) > 0


@pytest.mark.asyncio
async def test_search_by_title(setup_notes):
    """Test searching by note title."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results = searcher.search("Async")
    assert len(results) >= 2  # At least Python and JavaScript notes
    
    # Check that results are sorted by score
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


@pytest.mark.asyncio
async def test_search_by_content(setup_notes):
    """Test searching by note content."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results = searcher.search("Docker")
    assert len(results) >= 1
    assert any("Docker" in r.title or "Docker" in r.content for r in results)


@pytest.mark.asyncio
async def test_search_with_project_filter(setup_notes):
    """Test searching within a specific project."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results = searcher.search("programming", project="Python")
    assert all(r.project == "Python" for r in results)


@pytest.mark.asyncio
async def test_search_fuzzy_matching(setup_notes):
    """Test fuzzy search matching."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    # Misspelled search should still find results
    results = searcher.search("asynk", threshold=50)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_search_no_results(setup_notes):
    """Test search with no matching results."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results = searcher.search("NonexistentTopic")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_excerpt_generation(setup_notes):
    """Test that search results include relevant excerpts."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results = searcher.search("Docker")
    if results:
        assert results[0].excerpt is not None
        assert len(results[0].excerpt) > 0


@pytest.mark.asyncio
async def test_search_case_insensitive(setup_notes):
    """Test that search is case-insensitive."""
    storage, searcher = setup_notes
    await searcher.rebuild_index()
    
    results_lower = searcher.search("docker")
    results_upper = searcher.search("DOCKER")
    results_mixed = searcher.search("Docker")
    
    assert len(results_lower) == len(results_upper) == len(results_mixed)
