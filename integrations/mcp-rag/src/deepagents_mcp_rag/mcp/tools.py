"""MCP Tools implementation - Command pattern for full RAG workflows."""

import time
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

from ..retrievers.factory import RetrieverFactory


async def research_deep(
    question: str,
    strategy: str = "auto",
    max_results: int = 5,
    include_sources: bool = True,
    enable_evaluation: bool = True
) -> Dict[str, Any]:
    """Execute deep research using DeepAgents with multi-strategy RAG.

    This is the main command tool that provides complete RAG pipeline
    with DeepAgents orchestration, synthesis, and evaluation.

    Args:
        question: Research question to investigate
        strategy: Retrieval strategy (auto, bm25, vector, parent_doc, multi_query, rerank, ensemble)
        max_results: Maximum number of documents to retrieve
        include_sources: Whether to include source documents in response
        enable_evaluation: Whether to run RAGAS evaluation on the result

    Returns:
        Complete research result with answer, sources, and metrics
    """
    from ..agent import create_research_agent
    from ..eval import calculate_ragas_metrics
    from ..utils.logging import get_logger

    logger = get_logger(__name__)
    start_time = time.time()

    try:
        # Step 1: Create research agent with RAG capabilities
        agent = await create_research_agent(
            retrieval_strategy=strategy,
            max_results=max_results
        )

        # Step 2: Execute research with DeepAgents orchestration
        logger.info(f"Starting deep research for: {question[:100]}...")

        research_result = await agent.arun(
            f"Research the following question comprehensively: {question}"
        )

        # Step 3: Extract structured information
        answer = research_result.get("output", research_result)
        retrieved_docs = research_result.get("retrieved_documents", [])

        # Step 4: Calculate performance metrics
        total_time = time.time() - start_time

        result = {
            "answer": answer,
            "question": question,
            "strategy_used": strategy,
            "num_sources": len(retrieved_docs),
            "processing_time_seconds": round(total_time, 2),
            "timestamp": time.time()
        }

        # Step 5: Include sources if requested
        if include_sources and retrieved_docs:
            result["sources"] = [
                {
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "rank": i + 1
                }
                for i, doc in enumerate(retrieved_docs[:max_results])
            ]

        # Step 6: Run RAGAS evaluation if enabled
        if enable_evaluation and retrieved_docs:
            try:
                ragas_scores = await calculate_ragas_metrics(
                    question=question,
                    answer=answer,
                    contexts=[doc.page_content for doc in retrieved_docs]
                )
                result["ragas_scores"] = ragas_scores

            except Exception as e:
                logger.warning(f"RAGAS evaluation failed: {e}")
                result["ragas_scores"] = {"error": str(e)}

        logger.info(f"Deep research completed in {total_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Deep research failed: {e}")
        return {
            "error": str(e),
            "question": question,
            "strategy_attempted": strategy,
            "processing_time_seconds": time.time() - start_time
        }


async def evaluate_rag(
    strategy: str = "ensemble",
    num_test_cases: int = 10,
    output_format: str = "summary"
) -> Dict[str, Any]:
    """Evaluate RAG system performance using RAGAS metrics.

    Args:
        strategy: Retrieval strategy to evaluate
        num_test_cases: Number of test cases to run
        output_format: Output format (summary, detailed, json)

    Returns:
        Evaluation results with RAGAS metrics
    """
    from ..eval import RAGASEvaluator, load_golden_dataset
    from ..utils.logging import get_logger

    logger = get_logger(__name__)
    start_time = time.time()

    try:
        # Step 1: Load test dataset
        dataset = await load_golden_dataset(limit=num_test_cases)
        if not dataset:
            return {
                "error": "No test dataset available. Please create golden_set.jsonl",
                "suggestion": "Run the dataset generation script to create test cases"
            }

        # Step 2: Initialize evaluator
        evaluator = RAGASEvaluator(strategy=strategy)

        # Step 3: Run evaluation
        logger.info(f"Starting RAGAS evaluation with {len(dataset)} test cases...")

        results = await evaluator.evaluate_dataset(dataset)

        # Step 4: Format results based on output_format
        if output_format == "summary":
            return {
                "strategy": strategy,
                "test_cases": len(dataset),
                "overall_score": results["overall_score"],
                "metrics": {
                    "answer_relevancy": results["answer_relevancy"],
                    "context_precision": results["context_precision"],
                    "context_recall": results["context_recall"],
                    "faithfulness": results["faithfulness"]
                },
                "evaluation_time_seconds": round(time.time() - start_time, 2),
                "timestamp": time.time()
            }

        elif output_format == "detailed":
            return {
                "strategy": strategy,
                "summary": results,
                "detailed_results": results.get("detailed_results", []),
                "evaluation_time_seconds": round(time.time() - start_time, 2)
            }

        else:  # json format
            return results

    except Exception as e:
        logger.error(f"RAG evaluation failed: {e}")
        return {
            "error": str(e),
            "strategy": strategy,
            "evaluation_time_seconds": time.time() - start_time
        }


async def strategy_compare(
    question: str,
    strategies: Optional[List[str]] = None,
    max_results: int = 5
) -> Dict[str, Any]:
    """Compare multiple retrieval strategies for a given question.

    Args:
        question: Question to use for strategy comparison
        strategies: List of strategies to compare (default: all available)
        max_results: Maximum results per strategy

    Returns:
        Comprehensive comparison of strategy performance
    """
    from ..utils.logging import get_logger
    import asyncio

    logger = get_logger(__name__)
    start_time = time.time()

    if strategies is None:
        strategies = ["bm25", "vector", "parent_doc", "multi_query", "rerank", "ensemble"]

    try:
        # Step 1: Execute all strategies in parallel
        logger.info(f"Comparing {len(strategies)} strategies for: {question[:100]}...")

        async def run_strategy(strategy: str) -> Dict[str, Any]:
            """Run a single strategy and capture metrics."""
            strategy_start = time.time()

            try:
                retriever = RetrieverFactory.create(strategy, k=max_results)
                documents = await retriever.retrieve(question)

                return {
                    "strategy": strategy,
                    "success": True,
                    "num_results": len(documents),
                    "latency_ms": round((time.time() - strategy_start) * 1000, 2),
                    "documents": [
                        {
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "metadata": doc.metadata,
                            "rank": i + 1
                        }
                        for i, doc in enumerate(documents[:3])  # Top 3 for comparison
                    ]
                }

            except Exception as e:
                return {
                    "strategy": strategy,
                    "success": False,
                    "error": str(e),
                    "latency_ms": round((time.time() - strategy_start) * 1000, 2)
                }

        # Step 2: Run strategies in parallel
        strategy_tasks = [run_strategy(strategy) for strategy in strategies]
        strategy_results = await asyncio.gather(*strategy_tasks)

        # Step 3: Analyze results
        successful_strategies = [r for r in strategy_results if r["success"]]
        failed_strategies = [r for r in strategy_results if not r["success"]]

        # Calculate performance rankings
        if successful_strategies:
            # Rank by latency (ascending)
            latency_ranking = sorted(successful_strategies, key=lambda x: x["latency_ms"])

            # Rank by number of results (descending)
            results_ranking = sorted(successful_strategies, key=lambda x: x["num_results"], reverse=True)

        else:
            latency_ranking = []
            results_ranking = []

        # Step 4: Generate recommendations
        recommendations = _generate_strategy_recommendations(
            question, successful_strategies, failed_strategies
        )

        total_time = time.time() - start_time

        return {
            "question": question,
            "strategies_compared": strategies,
            "successful_strategies": len(successful_strategies),
            "failed_strategies": len(failed_strategies),
            "performance_rankings": {
                "fastest": latency_ranking,
                "most_results": results_ranking
            },
            "strategy_results": strategy_results,
            "recommendations": recommendations,
            "total_comparison_time_seconds": round(total_time, 2),
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Strategy comparison failed: {e}")
        return {
            "error": str(e),
            "question": question,
            "strategies_attempted": strategies,
            "comparison_time_seconds": time.time() - start_time
        }


def _generate_strategy_recommendations(
    question: str,
    successful_strategies: List[Dict[str, Any]],
    failed_strategies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate strategy recommendations based on comparison results.

    Args:
        question: Original question
        successful_strategies: Strategies that succeeded
        failed_strategies: Strategies that failed

    Returns:
        Dictionary with recommendations and reasoning
    """
    if not successful_strategies:
        return {
            "primary_recommendation": "ensemble",
            "reasoning": "All strategies failed - ensemble provides best fallback coverage",
            "fallback_options": ["vector", "bm25"],
            "issues_detected": [s["error"] for s in failed_strategies]
        }

    # Find fastest strategy
    fastest = min(successful_strategies, key=lambda x: x["latency_ms"])

    # Find most comprehensive (most results)
    most_comprehensive = max(successful_strategies, key=lambda x: x["num_results"])

    # Analyze query characteristics
    query_lower = question.lower()
    query_type = "general"

    if any(keyword in query_lower for keyword in ["what", "when", "where", "who"]):
        query_type = "factual"
        primary_rec = "bm25"
        reasoning = "Factual question - BM25 excels at exact keyword matching"

    elif any(keyword in query_lower for keyword in ["how", "why", "explain"]):
        query_type = "conceptual"
        primary_rec = "ensemble"
        reasoning = "Conceptual question - ensemble provides comprehensive coverage"

    elif any(term in query_lower for term in ["function", "class", "api", "error", "bug"]):
        query_type = "technical"
        primary_rec = "parent_doc"
        reasoning = "Technical question - parent document preserves code context"

    else:
        primary_rec = "ensemble"
        reasoning = "General question - ensemble provides optimal balance"

    # Ensure recommendation is in successful strategies
    if primary_rec not in [s["strategy"] for s in successful_strategies]:
        primary_rec = fastest["strategy"]
        reasoning = f"Fallback to fastest successful strategy: {primary_rec}"

    return {
        "primary_recommendation": primary_rec,
        "reasoning": reasoning,
        "query_type": query_type,
        "performance_insights": {
            "fastest_strategy": fastest["strategy"],
            "fastest_time_ms": fastest["latency_ms"],
            "most_comprehensive": most_comprehensive["strategy"],
            "most_results": most_comprehensive["num_results"]
        },
        "alternative_options": [
            s["strategy"] for s in successful_strategies
            if s["strategy"] != primary_rec
        ][:3]  # Top 3 alternatives
    }