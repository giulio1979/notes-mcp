import os
import logging
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None
    embedding_functions = None

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persistence_path: str = "chroma_db"):
        if chromadb is None:
            logger.error("chromadb not installed. Vector search will not work.")
            self.client = None
            self.collection = None
            return

        try:
            self.client = chromadb.PersistentClient(path=persistence_path)
            
            # Use all-MiniLM-L6-v2 which is lightweight and effective
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self.collection = self.client.get_or_create_collection(
                name="notes_embeddings",
                embedding_function=self.embedding_function
            )
            logger.info(f"Vector store initialized at {persistence_path}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.client = None
            self.collection = None

    def add_note(self, project: str, title: str, content: str, metadata: Dict[str, Any] = None):
        """Add or update a note in the vector store."""
        if self.collection is None:
            return

        if metadata is None:
            metadata = {}
        
        # Ensure project and title are in metadata
        metadata["project"] = project
        metadata["title"] = title
        
        # Create a unique ID for the note
        note_id = f"{project}/{title}"

        try:
            self.collection.upsert(
                documents=[content],
                metadatas=[metadata],
                ids=[note_id]
            )
            logger.debug(f"Upserted note {note_id} into vector store")
        except Exception as e:
            logger.error(f"Error adding note to vector store: {e}")

    def delete_note(self, project: str, title: str):
        """Delete a note from the vector store."""
        if self.collection is None:
            return
            
        note_id = f"{project}/{title}"
        try:
            self.collection.delete(ids=[note_id])
            logger.debug(f"Deleted note {note_id} from vector store")
        except Exception as e:
            logger.error(f"Error deleting note from vector store: {e}")

    def search(self, query: str, project: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for notes semantically."""
        if self.collection is None:
            return []

        where_filter = None
        if project:
            where_filter = {"project": project}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            formatted_results = []
            if results["ids"]:
                # ChromaDB returns lists of lists (one list per query)
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def clear_all(self):
        """Clear all data from the vector store."""
        if self.client is None:
            return
            
        try:
            self.client.delete_collection("notes_embeddings")
            self.collection = self.client.get_or_create_collection(
                name="notes_embeddings",
                embedding_function=self.embedding_function
            )
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
