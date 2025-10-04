"""Tests for the storage module."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.storage import NotesStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = NotesStorage(base_dir=temp_dir)
    yield storage
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_store_and_retrieve_note(temp_storage):
    """Test storing and retrieving a note."""
    project = "Test Project"
    title = "Test Note"
    content = "This is a test note content."
    
    # Store the note
    filepath = await temp_storage.store_note(project, title, content)
    assert filepath is not None
    assert Path(filepath).exists()
    
    # Retrieve the note
    retrieved_content, timestamp = await temp_storage.retrieve_note(project, title)
    assert retrieved_content == content
    assert timestamp is not None


@pytest.mark.asyncio
async def test_versioning(temp_storage):
    """Test that multiple versions of a note are created."""
    project = "Test Project"
    title = "Versioned Note"
    
    # Store first version
    content1 = "Version 1 content"
    await temp_storage.store_note(project, title, content1)
    
    # Store second version
    content2 = "Version 2 content"
    await temp_storage.store_note(project, title, content2)
    
    # Retrieve latest version
    retrieved_content, _ = await temp_storage.retrieve_note(project, title)
    assert retrieved_content == content2


@pytest.mark.asyncio
async def test_retrieve_nonexistent_note(temp_storage):
    """Test retrieving a note that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        await temp_storage.retrieve_note("Nonexistent Project", "Nonexistent Note")


def test_list_projects(temp_storage):
    """Test listing projects."""
    # Initially empty
    projects = temp_storage.list_projects()
    assert projects == []
    
    # Create project directories
    temp_storage._get_project_dir("Project 1")
    temp_storage._get_project_dir("Project 2")
    
    projects = temp_storage.list_projects()
    assert len(projects) == 2
    assert "Project 1" in projects or "Project_1" in projects


@pytest.mark.asyncio
async def test_list_notes(temp_storage):
    """Test listing notes in a project."""
    project = "Test Project"
    
    # Store some notes
    await temp_storage.store_note(project, "Note 1", "Content 1")
    await temp_storage.store_note(project, "Note 2", "Content 2")
    
    # List notes
    notes = temp_storage.list_notes(project)
    assert len(notes) == 2
    
    titles = [note["title"] for note in notes]
    assert "Note 1" in titles
    assert "Note 2" in titles


def test_sanitize_filename(temp_storage):
    """Test that filenames are properly sanitized."""
    project = "Test/Project:With:Special*Chars"
    title = "Note<>With|Bad?Chars"
    
    # Should not raise exception
    project_dir = temp_storage._get_project_dir(project)
    assert project_dir.exists()
    
    filename = temp_storage._generate_filename(title)
    assert "/" not in filename
    assert ":" not in filename
    assert "*" not in filename
