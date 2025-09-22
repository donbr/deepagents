#!/usr/bin/env python3
"""Minimal MCP server for testing Claude Code integration - HTTP version"""

from fastmcp import FastMCP
import asyncio

mcp = FastMCP("Test")

@mcp.tool()
async def test_connection() -> str:
    """Test if MCP connection is working"""
    return "✅ MCP connection successful! DeepAgents RAG server is working."

@mcp.tool()
async def simple_benchmark() -> str:
    """Run a simple performance test"""
    import time

    start = time.perf_counter()
    await asyncio.sleep(0.005)  # 5ms simulated work
    end = time.perf_counter()

    latency_ms = (end - start) * 1000
    return f"Benchmark complete: {latency_ms:.1f}ms latency"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)