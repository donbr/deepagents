"""DeepAgents integration for RAG system."""

from typing import Dict, Any, List, Optional
from deepagents import create_deep_agent, SubAgent
from langchain_core.tools import Tool

from .prompts import RESEARCH_AGENT_INSTRUCTIONS, RAG_SYSTEM_PROMPT
from ..retrievers.factory import RetrieverFactory
from ..utils.logging import get_logger


async def create_research_agent(
    retrieval_strategy: str = "auto",
    max_results: int = 5,
    enable_cache: bool = True
) -> Any:
    """Create a DeepAgents research agent with RAG capabilities.

    Args:
        retrieval_strategy: Default retrieval strategy
        max_results: Maximum documents to retrieve
        enable_cache: Whether to enable caching

    Returns:
        Configured DeepAgents agent with RAG tools
    """
    logger = get_logger(__name__)

    # Create custom retrieval tools
    retrieval_tools = await _create_retrieval_tools(
        retrieval_strategy, max_results, enable_cache
    )

    # Create evaluation tools
    evaluation_tools = _create_evaluation_tools()

    # Combine all tools
    all_tools = retrieval_tools + evaluation_tools

    # Create research sub-agent
    research_subagent = SubAgent(
        name="rag_researcher",
        description="Expert at retrieving and analyzing documents using multi-strategy RAG",
        tools=retrieval_tools,
        prompt=RESEARCH_AGENT_INSTRUCTIONS
    )

    # Create evaluation sub-agent
    evaluation_subagent = SubAgent(
        name="quality_evaluator",
        description="Evaluates research quality using RAGAS metrics",
        tools=evaluation_tools,
        prompt="You are an expert at evaluating research quality using RAGAS metrics."
    )

    try:
        # Create the main DeepAgent
        agent = await create_deep_agent(
            tools=all_tools,
            instructions=RAG_SYSTEM_PROMPT,
            subagents=[research_subagent, evaluation_subagent],
            model="claude-sonnet-4-20250514",
            builtin_tools=["write_todos", "read_file", "write_file"]
        )

        logger.info("Created DeepAgents research agent with RAG capabilities")
        return agent

    except ImportError:
        logger.warning("DeepAgents not available, creating fallback agent")
        return await _create_fallback_agent(all_tools)


async def create_deep_agent_with_rag(
    instructions: Optional[str] = None,
    subagents: Optional[List[SubAgent]] = None,
    additional_tools: Optional[List[Tool]] = None,
    **kwargs
) -> Any:
    """Create a DeepAgent with integrated RAG capabilities.

    Args:
        instructions: Custom instructions for the agent
        subagents: Additional sub-agents to include
        additional_tools: Additional tools beyond RAG tools
        **kwargs: Additional arguments for create_deep_agent

    Returns:
        Configured DeepAgent with RAG integration
    """
    logger = get_logger(__name__)

    # Create RAG tools
    rag_tools = await _create_retrieval_tools()

    # Combine tools
    all_tools = rag_tools
    if additional_tools:
        all_tools.extend(additional_tools)

    # Default instructions if not provided
    if instructions is None:
        instructions = RAG_SYSTEM_PROMPT

    # Default sub-agents
    default_subagents = [
        SubAgent(
            name="rag_specialist",
            description="Specialist in multi-strategy document retrieval and analysis",
            tools=rag_tools,
            prompt=RESEARCH_AGENT_INSTRUCTIONS
        )
    ]

    if subagents:
        default_subagents.extend(subagents)

    try:
        # Create DeepAgent
        agent = await create_deep_agent(
            tools=all_tools,
            instructions=instructions,
            subagents=default_subagents,
            **kwargs
        )

        logger.info("Created DeepAgent with integrated RAG capabilities")
        return agent

    except ImportError:
        logger.warning("DeepAgents not available, using fallback")
        return await _create_fallback_agent(all_tools)


async def _create_retrieval_tools(
    default_strategy: str = "auto",
    max_results: int = 5,
    enable_cache: bool = True
) -> List[Tool]:
    """Create LangChain tools for retrieval strategies.

    Args:
        default_strategy: Default retrieval strategy
        max_results: Maximum documents to retrieve
        enable_cache: Whether to enable caching

    Returns:
        List of retrieval tools
    """
    tools = []

    # Tool for flexible retrieval with strategy selection
    async def retrieve_documents(query: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve documents using specified strategy.

        Args:
            query: Search query
            strategy: Retrieval strategy (optional)

        Returns:
            Retrieved documents with metadata
        """
        if strategy is None:
            strategy = default_strategy

        retriever = RetrieverFactory.create(
            strategy=strategy,
            k=max_results,
            enable_caching=enable_cache
        )

        documents = await retriever.retrieve(query)

        return {
            "query": query,
            "strategy": strategy,
            "num_documents": len(documents),
            "documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "rank": i + 1
                }
                for i, doc in enumerate(documents)
            ]
        }

    tools.append(
        Tool(
            name="retrieve_documents",
            description="Retrieve documents using multi-strategy RAG",
            func=lambda q, s=None: retrieve_documents(q, s),
            coroutine=retrieve_documents
        )
    )

    # Tool for strategy comparison
    async def compare_strategies(query: str) -> Dict[str, Any]:
        """Compare retrieval strategies for a query.

        Args:
            query: Search query

        Returns:
            Comparison results across strategies
        """
        from ..mcp.tools import strategy_compare
        return await strategy_compare(query)

    tools.append(
        Tool(
            name="compare_strategies",
            description="Compare multiple retrieval strategies",
            func=lambda q: compare_strategies(q),
            coroutine=compare_strategies
        )
    )

    # Tool for strategy recommendation
    def get_strategy_recommendation(query: str) -> Dict[str, Any]:
        """Get strategy recommendation for a query.

        Args:
            query: Search query

        Returns:
            Recommended strategy with reasoning
        """
        return RetrieverFactory.get_strategy_recommendations(query)

    tools.append(
        Tool(
            name="get_strategy_recommendation",
            description="Get optimal retrieval strategy recommendation",
            func=get_strategy_recommendation
        )
    )

    return tools


def _create_evaluation_tools() -> List[Tool]:
    """Create evaluation and quality assessment tools.

    Returns:
        List of evaluation tools
    """
    tools = []

    # Tool for RAGAS evaluation
    async def evaluate_response(
        question: str,
        answer: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """Evaluate response quality using RAGAS.

        Args:
            question: Original question
            answer: Generated answer
            contexts: Retrieved contexts

        Returns:
            RAGAS evaluation metrics
        """
        from ..eval import calculate_ragas_metrics
        return await calculate_ragas_metrics(question, answer, contexts)

    tools.append(
        Tool(
            name="evaluate_response",
            description="Evaluate response quality using RAGAS metrics",
            func=lambda q, a, c: evaluate_response(q, a, c),
            coroutine=evaluate_response
        )
    )

    return tools


async def _create_fallback_agent(tools: List[Tool]) -> Dict[str, Any]:
    """Create a fallback agent when DeepAgents is not available.

    Args:
        tools: List of tools to include

    Returns:
        Simple agent-like structure
    """
    from ..utils.llm import get_llm

    llm = get_llm()

    return {
        "llm": llm,
        "tools": tools,
        "arun": lambda prompt: _simple_agent_run(llm, tools, prompt)
    }


async def _simple_agent_run(llm, tools, prompt: str) -> Dict[str, Any]:
    """Simple agent execution without DeepAgents.

    Args:
        llm: Language model
        tools: Available tools
        prompt: User prompt

    Returns:
        Agent response
    """
    # Basic implementation for fallback
    # In production, this would be more sophisticated

    # Extract query from prompt
    query = prompt

    # Find and execute retrieve_documents tool
    for tool in tools:
        if tool.name == "retrieve_documents":
            retrieval_result = await tool.coroutine(query)
            break
    else:
        retrieval_result = {"documents": []}

    # Generate response using LLM
    if retrieval_result["documents"]:
        context = "\n\n".join([
            f"Document {doc['rank']}: {doc['content']}"
            for doc in retrieval_result["documents"]
        ])

        full_prompt = f"""Answer this question based on the retrieved documents:

Question: {query}

Retrieved Documents:
{context}

Provide a comprehensive answer with citations."""

        response = await llm.ainvoke(full_prompt)
        answer = response.content

    else:
        answer = "No relevant documents found for your query."

    return {
        "output": answer,
        "retrieved_documents": retrieval_result.get("documents", [])
    }