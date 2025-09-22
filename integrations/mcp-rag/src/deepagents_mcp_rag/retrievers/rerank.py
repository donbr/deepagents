"""LLM-based reranking retrieval strategy.

Combines initial retrieval with LLM-based reranking for highest precision
by understanding query-document relevance at a deeper level.
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from .base import BaseRetriever


class RerankRetriever(BaseRetriever):
    """LLM-based reranking retrieval for maximum precision.

    Performs initial retrieval with a fast method, then uses an LLM to
    rerank results based on relevance to the query. Excellent for:
    - High-precision requirements
    - Complex relevance judgments
    - Cases where accuracy is more important than speed

    Performance characteristics:
    - Latency: ~200ms (base retrieval + LLM reranking)
    - Best for: High precision, complex relevance
    - Weakness: Higher cost, slower than base methods
    """

    def __init__(
        self,
        k: int = 5,
        initial_k: int = 20,
        base_retriever_strategy: str = "vector",
        rerank_prompt_template: Optional[str] = None,
        collection_name: str = "deepagents_documents",
        **kwargs
    ):
        """Initialize reranking retriever.

        Args:
            k: Final number of documents to return
            initial_k: Number of documents to retrieve before reranking
            base_retriever_strategy: Strategy for initial retrieval
            rerank_prompt_template: Custom reranking prompt
            collection_name: Vector store collection name
            **kwargs: Base retriever arguments
        """
        super().__init__(k=k, **kwargs)
        self.initial_k = max(initial_k, k * 2)  # Ensure enough candidates
        self.base_retriever_strategy = base_retriever_strategy
        self.collection_name = collection_name

        self.rerank_prompt_template = rerank_prompt_template or self._get_default_prompt()
        self._base_retriever = None
        self._llm = None

    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implement reranking retrieval.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of reranked documents
        """
        # Ensure components are initialized
        await self._ensure_components_initialized()

        if not self._base_retriever:
            return []

        try:
            # Step 1: Initial retrieval with base strategy
            initial_docs = await self._base_retriever.retrieve(query)

            if not initial_docs:
                return []

            # Step 2: LLM-based reranking
            if self._llm and len(initial_docs) > 1:
                reranked_docs = await self._rerank_documents(query, initial_docs)
            else:
                # Fallback to initial results if LLM not available
                reranked_docs = initial_docs

            # Step 3: Add reranking metadata
            final_docs = []
            for i, doc in enumerate(reranked_docs[:self.k]):
                doc.metadata = doc.metadata.copy()
                doc.metadata.update({
                    "retrieval_strategy": "rerank",
                    "base_strategy": self.base_retriever_strategy,
                    "rank": i + 1,
                    "reranked": self._llm is not None,
                    "initial_candidates": len(initial_docs)
                })
                final_docs.append(doc)

            return final_docs

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Reranking retrieval failed: {e}")
            return []

    async def _rerank_documents(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Document]:
        """Rerank documents using LLM.

        Args:
            query: Search query
            documents: Documents to rerank

        Returns:
            Reranked list of documents
        """
        if not self._llm or len(documents) <= 1:
            return documents

        try:
            # Create document candidates text
            candidates = []
            for i, doc in enumerate(documents):
                # Truncate content to avoid token limits
                content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                candidates.append(f"Document {i+1}:\n{content}")

            candidates_text = "\n\n".join(candidates)

            # Create reranking prompt
            prompt = PromptTemplate(
                input_variables=["query", "candidates", "num_docs"],
                template=self.rerank_prompt_template
            )

            prompt_text = prompt.format(
                query=query,
                candidates=candidates_text,
                num_docs=len(documents)
            )

            # Get LLM response
            response = await self._llm.ainvoke(prompt_text)
            ranking = self._parse_ranking_response(response.content, len(documents))

            # Reorder documents based on ranking
            reranked_docs = []
            for rank in ranking:
                if 1 <= rank <= len(documents):
                    doc = documents[rank - 1]  # Convert to 0-based index
                    # Add reranking score
                    doc.metadata = doc.metadata.copy()
                    doc.metadata["rerank_score"] = len(ranking) - len(reranked_docs)
                    reranked_docs.append(doc)

            # Add any missing documents at the end
            included_indices = {rank - 1 for rank in ranking if 1 <= rank <= len(documents)}
            for i, doc in enumerate(documents):
                if i not in included_indices:
                    doc.metadata = doc.metadata.copy()
                    doc.metadata["rerank_score"] = 0
                    reranked_docs.append(doc)

            return reranked_docs

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"LLM reranking failed: {e}")
            return documents  # Return original order on failure

    def _parse_ranking_response(self, response: str, num_docs: int) -> List[int]:
        """Parse LLM ranking response to extract document order.

        Args:
            response: LLM response text
            num_docs: Number of documents

        Returns:
            List of document indices in ranked order
        """
        ranking = []
        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            # Look for patterns like "1.", "Document 1", etc.
            for word in line.split():
                if word.isdigit():
                    num = int(word)
                    if 1 <= num <= num_docs and num not in ranking:
                        ranking.append(num)
                        break
                elif word.rstrip('.,)').isdigit():
                    num = int(word.rstrip('.,)'))
                    if 1 <= num <= num_docs and num not in ranking:
                        ranking.append(num)
                        break

        # Fill in missing numbers
        for i in range(1, num_docs + 1):
            if i not in ranking:
                ranking.append(i)

        return ranking

    async def _ensure_components_initialized(self) -> None:
        """Ensure base retriever and LLM are initialized."""
        if self._base_retriever is None:
            try:
                from .factory import RetrieverFactory

                self._base_retriever = RetrieverFactory.create(
                    self.base_retriever_strategy,
                    k=self.initial_k,
                    collection_name=self.collection_name
                )

            except Exception as e:
                from ..utils.logging import get_logger
                logger = get_logger(__name__)
                logger.error(f"Failed to initialize base retriever: {e}")

        if self._llm is None:
            try:
                from ..utils.llm import get_llm
                self._llm = get_llm()

            except Exception as e:
                from ..utils.logging import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Failed to initialize LLM for reranking: {e}")

    def _get_default_prompt(self) -> str:
        """Get default reranking prompt template."""
        return """You are an expert at ranking search results by relevance.

Given a search query and a list of candidate documents, rank them from most relevant to least relevant.

Query: {query}

Documents:
{candidates}

Instructions:
1. Analyze how well each document answers or relates to the query
2. Consider both semantic relevance and factual accuracy
3. Rank documents from 1 (most relevant) to {num_docs} (least relevant)
4. Provide only the ranking numbers, one per line

Ranking (most to least relevant):"""

    def get_info(self) -> Dict[str, Any]:
        """Get reranking retriever information."""
        info = super().get_info()
        info.update({
            "algorithm": "LLM-based Reranking",
            "initial_k": self.initial_k,
            "base_retriever_strategy": self.base_retriever_strategy,
            "collection_name": self.collection_name,
            "best_for": ["high_precision", "complex_relevance", "quality_over_speed"],
            "characteristics": {
                "latency": "~200ms",
                "accuracy": "highest_precision",
                "cost": "high"
            },
            "base_retriever_available": self._base_retriever is not None,
            "llm_available": self._llm is not None
        })
        return info

    async def get_reranking_explanation(
        self,
        query: str,
        documents: List[Document]
    ) -> Dict[str, Any]:
        """Get explanation of reranking decisions for debugging.

        Args:
            query: Search query
            documents: Documents to analyze

        Returns:
            Explanation of ranking decisions
        """
        await self._ensure_components_initialized()

        if not self._llm:
            return {"error": "LLM not available for explanations"}

        try:
            # Create explanation prompt
            candidates = []
            for i, doc in enumerate(documents):
                content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                candidates.append(f"Document {i+1}:\n{content}")

            candidates_text = "\n\n".join(candidates)

            explanation_prompt = f"""Analyze the relevance of these documents to the query and explain your ranking.

Query: {query}

Documents:
{candidates_text}

For each document, explain:
1. How relevant it is to the query (1-10 scale)
2. Key reasons for the relevance score
3. What information it provides related to the query

Provide detailed explanations:"""

            response = await self._llm.ainvoke(explanation_prompt)

            return {
                "query": query,
                "num_documents": len(documents),
                "explanation": response.content,
                "llm_model": getattr(self._llm, "model_name", "unknown")
            }

        except Exception as e:
            return {"error": f"Failed to generate explanation: {e}"}