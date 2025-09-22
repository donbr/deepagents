#!/usr/bin/env python3
"""
Debug script to check what tools are available from Tavily MCP server
"""

import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

async def debug_tavily_mcp():
    """Check what tools are available from Tavily MCP"""

    print("🔧 Debugging Tavily MCP server...")

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

        print("📦 Getting tools from MCP server...")
        tools = await client.get_tools()

        print(f"🔍 Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - Tool name: {tool.name}")
            print(f"    Description: {tool.description}")
            print(f"    Schema: {getattr(tool, 'input_schema', 'Not available')}")
            print("---")

        return tools

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(debug_tavily_mcp())