#!/usr/bin/env python3
"""
Simple test to verify MCP Tavily integration works
"""

import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_simple_search():
    """Test a simple search using MCP"""

    print("🔧 Testing simple MCP search...")

    try:
        client = MultiServerMCPClient({
            "tavily-remote": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "mcp-remote",
                    f"https://mcp.tavily.com/mcp/?tavilyApiKey={os.environ['TAVILY_API_KEY']}"
                ]
            }
        })

        tools = await client.get_tools()
        print(f"📦 Available tools: {[tool.name for tool in tools]}")

        # Find the search tool
        search_tool = None
        for tool in tools:
            if tool.name == "tavily_search":
                search_tool = tool
                break

        if not search_tool:
            print("❌ Search tool not found")
            return False

        print("🔍 Testing search...")

        # Test search
        result = await search_tool.ainvoke({
            "query": "What is MCP Model Context Protocol?",
            "max_results": 3
        })

        print(f"✅ Search successful!")
        print(f"Result type: {type(result)}")
        print(f"Result preview: {str(result)[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_simple_search())