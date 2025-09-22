"""Parent document retrieval strategy for hierarchical context.

Implements retrieval using small chunks for search but returns larger
parent documents for context preservation.
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain.retrievers import ParentDocumentRetriever as LangChainParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .base import BaseRetriever


class ParentDocRetriever(BaseRetriever):
    """Parent document retrieval for hierarchical context preservation.

    Uses small chunks for precise matching but returns larger parent
    documents to preserve context. Excellent for:
    - Code documentation where full context matters
    - Legal documents requiring surrounding context
    - Academic papers with section dependencies

    Performance characteristics:
    - Latency: ~50ms (due to chunk-to-parent mapping)
    - Best for: Context preservation, large documents
    - Weakness: Higher memory usage, more complex setup
    """

    def __init__(
        self,
        k: int = 5,
        child_chunk_size: int = 400,
        parent_chunk_size: int = 2000,
        chunk_overlap: int = 50,
        collection_name: str = "deepagents_documents",
        **kwargs
    ):
        """Initialize parent document retriever.

        Args:
            k: Number of parent documents to retrieve
            child_chunk_size: Size of child chunks for search
            parent_chunk_size: Size of parent chunks returned
            chunk_overlap: Overlap between chunks
            collection_name: Vector store collection name
            **kwargs: Base retriever arguments
        """
        super().__init__(k=k, **kwargs)
        self.child_chunk_size = child_chunk_size
        self.parent_chunk_size = parent_chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name

        self._parent_retriever = None
        self._child_splitter = None
        self._parent_splitter = None
        self._doc_store = None

    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implement parent document retrieval.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of parent documents with preserved context
        """
        # Ensure retriever is initialized
        await self._ensure_retriever_initialized()

        if not self._parent_retriever:
            return []

        try:
            # Use the parent document retriever
            documents = await self._parent_retriever.aget_relevant_documents(query)

            # Limit to k documents
            if len(documents) > self.k:
                documents = documents[:self.k]

            # Add metadata
            for i, doc in enumerate(documents):
                doc.metadata = doc.metadata.copy()
                doc.metadata.update({
                    "retrieval_strategy": "parent_doc",
                    "rank": i + 1,
                    "child_chunk_size": self.child_chunk_size,
                    "parent_chunk_size": self.parent_chunk_size,
                    "collection": self.collection_name
                })

            return documents

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Parent document retrieval failed: {e}")
            return []

    async def _ensure_retriever_initialized(self) -> None:
        """Ensure parent document retriever is initialized."""
        if self._parent_retriever is not None:
            return

        try:
            from ..utils.embeddings import get_embeddings
            from ..utils.vector_store import get_qdrant_client
            from langchain_qdrant import QdrantVectorStore

            # Initialize text splitters
            self._child_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.child_chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            self._parent_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.parent_chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            # Initialize document store for parent-child mapping
            self._doc_store = InMemoryStore()

            # Initialize vector store for child chunks
            embeddings = get_embeddings()
            qdrant_client = get_qdrant_client()

            child_vectorstore = QdrantVectorStore(
                client=qdrant_client,
                collection_name=f"{self.collection_name}_child_chunks",
                embeddings=embeddings
            )

            # Initialize parent document retriever
            self._parent_retriever = LangChainParentDocumentRetriever(
                vectorstore=child_vectorstore,
                docstore=self._doc_store,
                child_splitter=self._child_splitter,
                parent_splitter=self._parent_splitter,
                k=self.k
            )

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize parent document retriever: {e}")
            self._parent_retriever = None

    def get_info(self) -> Dict[str, Any]:
        """Get parent document retriever information."""
        info = super().get_info()
        info.update({
            "algorithm": "Hierarchical Parent-Child Retrieval",
            "child_chunk_size": self.child_chunk_size,
            "parent_chunk_size": self.parent_chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "collection_name": self.collection_name,
            "best_for": ["context_preservation", "large_documents", "code_docs"],
            "characteristics": {
                "latency": "~50ms",
                "accuracy": "high_with_context",
                "context_preservation": "excellent"
            },
            "retriever_initialized": self._parent_retriever is not None
        })
        return info

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the parent-child retrieval system.

        Args:
            documents: Documents to add and split into parent-child hierarchy
        """
        await self._ensure_retriever_initialized()

        if not self._parent_retriever:
            return

        try:
            # Add documents to the parent retriever
            # This will automatically split them into parent-child chunks
            await self._parent_retriever.aadd_documents(documents)

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to add documents to parent retriever: {e}")

    async def get_child_chunks(self, query: str, k: int = 10) -> List[Document]:
        """Get child chunks that match the query (for debugging).

        Args:
            query: Search query
            k: Number of child chunks to retrieve

        Returns:
            List of matching child chunks
        """
        await self._ensure_retriever_initialized()

        if not self._parent_retriever:
            return []

        try:
            # Access the underlying vectorstore to get child chunks
            vectorstore = self._parent_retriever.vectorstore
            child_chunks = await vectorstore.asimilarity_search(query, k=k)

            # Add metadata to indicate these are child chunks
            for i, chunk in enumerate(child_chunks):
                chunk.metadata = chunk.metadata.copy()
                chunk.metadata.update({
                    "chunk_type": "child",
                    "rank": i + 1,
                    "retrieval_strategy": "parent_doc_child"
                })

            return child_chunks

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to get child chunks: {e}")
            return []

    async def get_mapping_stats(self) -> Dict[str, Any]:
        """Get statistics about parent-child document mapping.

        Returns:
            Statistics about the document hierarchy
        """
        await self._ensure_retriever_initialized()

        if not self._parent_retriever or not self._doc_store:
            return {"error": "Retriever not initialized"}

        try:
            # Get basic statistics from the document store
            # Note: InMemoryStore doesn't have direct stats methods,
            # so we'll provide what we can
            return {
                "parent_chunk_size": self.parent_chunk_size,
                "child_chunk_size": self.child_chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "docstore_type": type(self._doc_store).__name__,
                "vectorstore_type": type(self._parent_retriever.vectorstore).__name__,
            }

        except Exception as e:
            return {"error": f"Failed to get mapping stats: {e}"}