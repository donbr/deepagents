"""Multi-query expansion retrieval strategy.

Generates multiple query perspectives to improve recall and coverage
for complex or ambiguous questions.
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain.retrievers import MultiQueryRetriever as LangChainMultiQueryRetriever
from langchain_core.prompts import PromptTemplate

from .base import BaseRetriever


class MultiQueryRetriever(BaseRetriever):
    """Multi-query expansion retrieval for comprehensive coverage.

    Generates multiple query variations to capture different perspectives
    and improve recall for complex topics. Excellent for:
    - Ambiguous or complex questions
    - Research requiring comprehensive coverage
    - Cases where multiple perspectives are valuable

    Performance characteristics:
    - Latency: ~100ms (2-3x base retrieval due to multiple queries)
    - Best for: Complex topics, comprehensive research
    - Weakness: Higher token usage, more expensive
    """

    def __init__(
        self,
        k: int = 5,
        num_queries: int = 3,
        base_retriever_strategy: str = "vector",
        collection_name: str = "deepagents_documents",
        **kwargs
    ):
        """Initialize multi-query retriever.

        Args:
            k: Number of documents to retrieve total
            num_queries: Number of query variations to generate
            base_retriever_strategy: Underlying retrieval strategy
            collection_name: Vector store collection name
            **kwargs: Base retriever arguments
        """
        super().__init__(k=k, **kwargs)
        self.num_queries = num_queries
        self.base_retriever_strategy = base_retriever_strategy
        self.collection_name = collection_name

        self._multi_query_retriever = None
        self._base_retriever = None
        self._llm = None

    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implement multi-query retrieval.

        Args:
            query: Original search query
            **kwargs: Additional parameters

        Returns:
            List of documents from all query variations, deduplicated
        """
        # Ensure retriever is initialized
        await self._ensure_retriever_initialized()

        if not self._multi_query_retriever:
            # Fallback to simple query if initialization failed
            await self._ensure_base_retriever()
            if self._base_retriever:
                return await self._base_retriever.retrieve(query)
            return []

        try:
            # Use multi-query retriever
            documents = await self._multi_query_retriever.aget_relevant_documents(query)

            # Limit to k documents and add metadata
            unique_docs = []
            seen_content = set()

            for doc in documents:
                # Simple deduplication based on content hash
                content_hash = hash(doc.page_content[:500])  # Use first 500 chars
                if content_hash not in seen_content and len(unique_docs) < self.k:
                    seen_content.add(content_hash)

                    # Add multi-query metadata
                    doc.metadata = doc.metadata.copy()
                    doc.metadata.update({
                        "retrieval_strategy": "multi_query",
                        "base_strategy": self.base_retriever_strategy,
                        "rank": len(unique_docs) + 1,
                        "num_queries_generated": self.num_queries
                    })
                    unique_docs.append(doc)

            return unique_docs

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Multi-query retrieval failed: {e}")

            # Fallback to base retriever
            await self._ensure_base_retriever()
            if self._base_retriever:
                return await self._base_retriever.retrieve(query)
            return []

    async def _ensure_retriever_initialized(self) -> None:
        """Ensure multi-query retriever is initialized."""
        if self._multi_query_retriever is not None:
            return

        try:
            from ..utils.llm import get_llm
            from .factory import RetrieverFactory

            # Get LLM for query generation
            self._llm = get_llm()

            # Initialize base retriever
            self._base_retriever = RetrieverFactory.create(
                self.base_retriever_strategy,
                k=self.k * 2,  # Get more docs to account for deduplication
                collection_name=self.collection_name
            )

            # Get the underlying LangChain retriever for MultiQueryRetriever
            base_langchain_retriever = await self._get_langchain_retriever()

            if base_langchain_retriever:
                # Create custom prompt for query generation
                query_prompt = PromptTemplate(
                    input_variables=["question"],
                    template="""You are an AI assistant helping to improve search queries.
                    Given the original question, generate {num_queries} different but related search queries
                    that would help find comprehensive information about the topic.

                    Make the queries:
                    1. Different in wording and perspective
                    2. Focused on different aspects of the topic
                    3. Specific enough to be useful for search

                    Original question: {question}

                    Generate exactly {num_queries} alternative search queries:""".format(
                        num_queries=self.num_queries
                    )
                )

                # Initialize MultiQueryRetriever
                self._multi_query_retriever = LangChainMultiQueryRetriever.from_llm(
                    retriever=base_langchain_retriever,
                    llm=self._llm,
                    prompt=query_prompt
                )

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize multi-query retriever: {e}")
            self._multi_query_retriever = None

    async def _get_langchain_retriever(self):
        """Get the underlying LangChain retriever from base retriever."""
        if not self._base_retriever:
            return None

        # Different base retrievers expose LangChain retrievers differently
        if hasattr(self._base_retriever, '_vector_store'):
            # Vector retriever
            return self._base_retriever._vector_store.as_retriever(
                search_kwargs={"k": self.k * 2}
            )
        elif hasattr(self._base_retriever, '_parent_retriever'):
            # Parent document retriever
            return self._base_retriever._parent_retriever
        else:
            # For other retrievers, create a simple wrapper
            return SimpleLangChainRetrieverWrapper(self._base_retriever)

    async def _ensure_base_retriever(self) -> None:
        """Ensure base retriever is available as fallback."""
        if self._base_retriever is not None:
            return

        try:
            from .factory import RetrieverFactory

            self._base_retriever = RetrieverFactory.create(
                self.base_retriever_strategy,
                k=self.k,
                collection_name=self.collection_name
            )

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize base retriever: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get multi-query retriever information."""
        info = super().get_info()
        info.update({
            "algorithm": "Multi-Query Expansion",
            "num_queries": self.num_queries,
            "base_retriever_strategy": self.base_retriever_strategy,
            "collection_name": self.collection_name,
            "best_for": ["complex_topics", "comprehensive_research", "ambiguous_queries"],
            "characteristics": {
                "latency": "~100ms",
                "accuracy": "high_recall",
                "token_usage": "high"
            },
            "retriever_initialized": self._multi_query_retriever is not None,
            "base_retriever_available": self._base_retriever is not None
        })
        return info

    async def get_generated_queries(self, query: str) -> List[str]:
        """Get the generated query variations for debugging.

        Args:
            query: Original query

        Returns:
            List of generated query variations
        """
        await self._ensure_retriever_initialized()

        if not self._llm:
            return [query]  # Return original query if LLM not available

        try:
            from langchain_core.prompts import PromptTemplate

            # Use the same prompt as the retriever
            query_prompt = PromptTemplate(
                input_variables=["question"],
                template="""You are an AI assistant helping to improve search queries.
                Given the original question, generate {num_queries} different but related search queries
                that would help find comprehensive information about the topic.

                Make the queries:
                1. Different in wording and perspective
                2. Focused on different aspects of the topic
                3. Specific enough to be useful for search

                Original question: {question}

                Generate exactly {num_queries} alternative search queries:""".format(
                    num_queries=self.num_queries
                )
            )

            # Generate queries
            prompt_text = query_prompt.format(question=query)
            response = await self._llm.ainvoke(prompt_text)

            # Parse response to extract queries
            queries = []
            lines = response.content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('You are', 'Given', 'Make', 'Original')):
                    # Remove numbering and clean up
                    cleaned = line.lstrip('0123456789.- ').strip()
                    if cleaned:
                        queries.append(cleaned)

            # Ensure we have the original query
            if query not in queries:
                queries.insert(0, query)

            return queries[:self.num_queries + 1]  # Include original + variations

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to generate query variations: {e}")
            return [query]


class SimpleLangChainRetrieverWrapper:
    """Simple wrapper to make our retrievers compatible with LangChain."""

    def __init__(self, retriever: BaseRetriever):
        self.retriever = retriever

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents using our retriever."""
        return await self.retriever.retrieve(query)

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Synchronous version (not implemented for async retrievers)."""
        raise NotImplementedError("Use aget_relevant_documents for async retrieval")