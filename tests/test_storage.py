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


@pytest.mark.asyncio
async def test_delete_all_versions(temp_storage):
    """Test deleting all versions of a note."""
    project = "Test Project"
    title = "Note To Delete"
    
    # Create multiple versions
    await temp_storage.store_note(project, title, "Version 1")
    await temp_storage.store_note(project, title, "Version 2")
    await temp_storage.store_note(project, title, "Version 3")
    
    # Verify they exist
    notes = temp_storage.list_notes(project)
    assert any(note["title"] == title for note in notes)
    
    # Delete all versions
    result = await temp_storage.delete_note(project, title)
    assert result["deleted"] == 3
    assert len(result["files"]) == 3
    
    # Verify they're gone
    notes = temp_storage.list_notes(project)
    assert not any(note["title"] == title for note in notes)


@pytest.mark.asyncio
async def test_delete_specific_version(temp_storage):
    """Test deleting a specific version of a note."""
    project = "Test Project"
    title = "Versioned Note"
    
    # Create first version
    await temp_storage.store_note(project, title, "Version 1")
    content1, version1 = await temp_storage.retrieve_note(project, title)
    
    # Create second version
    await temp_storage.store_note(project, title, "Version 2")
    content2, version2 = await temp_storage.retrieve_note(project, title)
    
    # Delete only the first version
    result = await temp_storage.delete_note(project, title, version1)
    assert result["deleted"] == 1
    
    # Verify second version still exists
    content, version = await temp_storage.retrieve_note(project, title)
    assert content == "Version 2"
    assert version == version2
    
    # Verify first version is gone
    with pytest.raises(FileNotFoundError):
        await temp_storage.retrieve_note(project, title, version1)


@pytest.mark.asyncio
async def test_delete_nonexistent_note(temp_storage):
    """Test deleting a note that doesn't exist."""
    project = "Test Project"
    title = "Nonexistent Note"
    
    with pytest.raises(FileNotFoundError):
        await temp_storage.delete_note(project, title)


@pytest.mark.asyncio
async def test_delete_note_leaves_other_notes(temp_storage):
    """Test that deleting one note doesn't affect others."""
    project = "Test Project"
    
    # Create multiple notes
    await temp_storage.store_note(project, "Note 1", "Content 1")
    await temp_storage.store_note(project, "Note 2", "Content 2")
    await temp_storage.store_note(project, "Note 3", "Content 3")
    
    # Delete one note
    await temp_storage.delete_note(project, "Note 2")
    
    # Verify others still exist
    notes = temp_storage.list_notes(project)
    titles = [note["title"] for note in notes]
    assert "Note 1" in titles
    assert "Note 2" not in titles
    assert "Note 3" in titles
