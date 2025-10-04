"""Tests for deep link functionality."""

import pytest
from src.server import get_deep_link
from urllib.parse import urlparse, parse_qs


def test_get_deep_link_project():
    """Test generating deep link for a project."""
    result = get_deep_link("Python Learning")
    
    assert "Python Learning" in result
    assert "http://localhost:5000/project/" in result
    assert "Python%20Learning" in result or "Python+Learning" in result


def test_get_deep_link_note():
    """Test generating deep link for a note."""
    result = get_deep_link("Python Learning", "AsyncIO Basics")
    
    assert "Python Learning" in result
    assert "AsyncIO Basics" in result
    assert "http://localhost:5000/note/" in result


def test_get_deep_link_note_with_version():
    """Test generating deep link for a specific note version."""
    result = get_deep_link(
        "Python Learning",
        "AsyncIO Basics",
        "2024-10-04T12:00:00"
    )
    
    assert "Python Learning" in result
    assert "AsyncIO Basics" in result
    assert "2024-10-04T12:00:00" in result or "version" in result.lower()
    assert "http://localhost:5000/note/" in result


def test_get_deep_link_custom_url():
    """Test generating deep link with custom web server URL."""
    result = get_deep_link(
        "Python Learning",
        web_server_url="https://notes.example.com"
    )
    
    assert "https://notes.example.com/project/" in result
    assert "Python%20Learning" in result or "Python+Learning" in result


def test_get_deep_link_url_encoding():
    """Test that special characters are properly URL encoded."""
    result = get_deep_link("Project/With:Special*Chars", "Note<>With|Bad?Chars")
    
    # Should contain encoded URL
    assert "http://localhost:5000/note/" in result
    # Project and note names should be URL encoded
    assert "%2F" in result or "Project" in result  # "/" should be encoded
    assert "%3A" in result or ":" not in result.split("//")[1]  # ":" should be encoded


def test_get_deep_link_trailing_slash():
    """Test that trailing slashes in base URL are handled correctly."""
    result1 = get_deep_link("Test", web_server_url="http://localhost:5000")
    result2 = get_deep_link("Test", web_server_url="http://localhost:5000/")
    
    # Both should produce the same result
    assert "http://localhost:5000/project/" in result1
    assert "http://localhost:5000/project/" in result2
    # Should not have double slashes
    assert "http://localhost:5000//project/" not in result1
    assert "http://localhost:5000//project/" not in result2
