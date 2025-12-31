import pytest
import os
import shutil
import uuid
from src.vector_store import VectorStore

@pytest.fixture
def vector_store():
    # Use a unique temporary directory for each test
    test_db_path = f"test_chroma_db_{uuid.uuid4()}"
    
    store = VectorStore(persistence_path=test_db_path)
    yield store
    
    # Cleanup
    if os.path.exists(test_db_path):
        try:
            shutil.rmtree(test_db_path)
        except PermissionError:
            # On Windows, files might still be locked. 
            # We can't do much about it in the test process.
            # They will be cleaned up by OS eventually or manually.
            pass 

def test_add_and_search(vector_store):
    if vector_store.client is None:
        pytest.skip("ChromaDB not installed or failed to initialize")

    vector_store.add_note(
        project="test_project",
        title="python_note",
        content="Python is a great programming language for data science.",
        metadata={"tag": "coding"}
    )
    
    vector_store.add_note(
        project="test_project",
        title="cooking_note",
        content="Pasta is a delicious Italian dish.",
        metadata={"tag": "food"}
    )
    
    # Search for python related content
    results = vector_store.search("programming", limit=1)
    
    assert len(results) == 1
    assert results[0]["metadata"]["title"] == "python_note"
    
    # Search for food related content
    results = vector_store.search("food", limit=1)
    assert len(results) == 1
    assert results[0]["metadata"]["title"] == "cooking_note"

def test_delete_note(vector_store):
    if vector_store.client is None:
        pytest.skip("ChromaDB not installed")

    vector_store.add_note("p1", "t1", "content")
    results = vector_store.search("content")
    assert len(results) == 1
    
    vector_store.delete_note("p1", "t1")
    results = vector_store.search("content")
    assert len(results) == 0
