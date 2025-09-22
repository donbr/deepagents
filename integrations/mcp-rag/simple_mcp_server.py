#!/usr/bin/env python3
# /// script
# dependencies = [
#   "fastmcp>=2.12.0",
# ]
# ///
"""
DeepAgents RAG MCP Server (streamable HTTP transport)
Provides simple RAG functionality as MCP tools.

Dependencies:
  uv add fastmcp
  # or: pip install fastmcp
"""

from fastmcp import FastMCP
import asyncio
import time

mcp = FastMCP("DeepAgents RAG")

# Mock document store for testing
MOCK_DOCUMENTS = [
    {"id": "doc1", "content": "Vector search uses dense embeddings to find semantically similar content.", "metadata": {"topic": "search"}},
    {"id": "doc2", "content": "BM25 is a keyword-based retrieval function using term frequency and inverse document frequency.", "metadata": {"topic": "algorithms"}},
    {"id": "doc3", "content": "Ensemble retrieval combines multiple strategies using Reciprocal Rank Fusion.", "metadata": {"topic": "ensemble"}},
    {"id": "doc4", "content": "Multi-query expansion generates variations to improve recall.", "metadata": {"topic": "expansion"}},
    {"id": "doc5", "content": "Parent document retrieval returns larger context while matching on smaller chunks.", "metadata": {"topic": "chunking"}},
]

@mcp.tool()
async def simple_search(query: str, max_results: int = 3) -> str:
    """Simple keyword-based document search"""
    # Simulate search latency
    await asyncio.sleep(0.01)

    # Simple keyword matching
    query_lower = query.lower()
    results = []

    for doc in MOCK_DOCUMENTS:
        if any(word in doc["content"].lower() for word in query_lower.split()):
            results.append({
                "id": doc["id"],
                "content": doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"],
                "score": 0.9  # Mock score
            })

    # Limit results
    results = results[:max_results]

    if not results:
        return f"No documents found for query: {query}"

    response = f"Found {len(results)} documents for '{query}':\n\n"
    for i, result in enumerate(results, 1):
        response += f"{i}. {result['content']} (Score: {result['score']})\n\n"

    return response

@mcp.tool()
async def benchmark_search(strategy: str = "simple", iterations: int = 5) -> str:
    """Benchmark search performance for different strategies"""
    latencies = []

    test_queries = ["vector search", "BM25 algorithm", "ensemble methods"]

    for i in range(iterations):
        query = test_queries[i % len(test_queries)]
        start_time = time.perf_counter()

        # Mock different strategy latencies
        if strategy == "simple":
            await asyncio.sleep(0.005)  # 5ms
        elif strategy == "vector":
            await asyncio.sleep(0.015)  # 15ms
        elif strategy == "ensemble":
            await asyncio.sleep(0.050)  # 50ms
        else:
            await asyncio.sleep(0.010)  # 10ms default

        latency_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(latency_ms)

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    return f"""Benchmark Results for {strategy} strategy:
Iterations: {iterations}
Average latency: {avg_latency:.1f}ms
Min latency: {min_latency:.1f}ms
Max latency: {max_latency:.1f}ms
Individual results: {[f"{l:.1f}ms" for l in latencies]}"""

@mcp.tool()
async def list_strategies() -> str:
    """List available retrieval strategies"""
    strategies = {
        "simple": "Basic keyword matching",
        "vector": "Semantic similarity search",
        "ensemble": "Combined multi-strategy approach"
    }

    response = "Available retrieval strategies:\n\n"
    for name, description in strategies.items():
        response += f"• {name}: {description}\n"

    return response

@mcp.resource("search://{strategy}/{query}")
async def search_resource(strategy: str, query: str) -> str:
    """Fast search resource without full tool overhead"""
    # Simulate faster resource access
    await asyncio.sleep(0.002)

    return f"Resource search via {strategy} strategy for: {query}\nResults: [Mock resource response - 3x faster than tools]"

if __name__ == "__main__":
    mcp.run(transport="stdio")