"""Document store utilities for managing document collections."""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from ..config import get_settings


class DocumentStore:
    """Document store for managing document collections."""

    def __init__(self):
        self._documents: List[Document] = []
        self._metadata: Dict[str, Any] = {}

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the store.

        Args:
            documents: Documents to add
        """
        self._documents.extend(documents)

    async def get_all_documents(self) -> List[Document]:
        """Get all documents from the store.

        Returns:
            List of all stored documents
        """
        return self._documents.copy()

    async def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Get a document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        for doc in self._documents:
            if doc.metadata.get("id") == doc_id:
                return doc
        return None

    async def search_documents(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        # Simple text search - in production, this would use proper indexing
        query_lower = query.lower()
        matches = []

        for doc in self._documents:
            if query_lower in doc.page_content.lower():
                matches.append(doc)
                if len(matches) >= limit:
                    break

        return matches

    async def remove_document(self, doc_id: str) -> bool:
        """Remove a document by ID.

        Args:
            doc_id: Document ID to remove

        Returns:
            True if document was removed, False if not found
        """
        for i, doc in enumerate(self._documents):
            if doc.metadata.get("id") == doc_id:
                del self._documents[i]
                return True
        return False

    async def clear(self) -> None:
        """Clear all documents from the store."""
        self._documents.clear()
        self._metadata.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get document store statistics.

        Returns:
            Dictionary with store statistics
        """
        total_chars = sum(len(doc.page_content) for doc in self._documents)
        avg_length = total_chars / len(self._documents) if self._documents else 0

        return {
            "total_documents": len(self._documents),
            "total_characters": total_chars,
            "average_document_length": avg_length,
            "metadata_keys": list(self._metadata.keys())
        }


# Global document store instance
_document_store = None


async def get_document_store() -> DocumentStore:
    """Get the global document store instance.

    Returns:
        DocumentStore instance
    """
    global _document_store

    if _document_store is None:
        _document_store = DocumentStore()

    return _document_store