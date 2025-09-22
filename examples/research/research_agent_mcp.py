#!/usr/bin/env python3
"""
DeepAgents Research Agent with MCP integration
Demonstrates replacing Tavily Python client with Tavily MCP server
"""

import asyncio
import os
from typing import Literal

from deepagents import async_create_deep_agent, SubAgent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Global MCP client and tools
mcp_client = None
search_tool = None

async def initialize_mcp():
    """Initialize MCP client and get search tool"""
    global mcp_client, search_tool

    if mcp_client is None:
        print("🔗 Initializing MCP client...")
        mcp_client = MultiServerMCPClient({
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

        tools = await mcp_client.get_tools()
        print(f"📦 Available MCP tools: {[tool.name for tool in tools]}")

        # Find the tavily_search tool
        for tool in tools:
            if tool.name == "tavily_search":
                search_tool = tool
                # Rename to match what the agent expects
                search_tool.name = "internet_search"
                break

        if not search_tool:
            raise RuntimeError("Tavily search tool not found in MCP server")

        print("✅ MCP integration ready!")

    return search_tool

# Sub-agent prompts (simplified for demo)
research_sub_agent = {
    "name": "research-agent",
    "description": "Used to research topics in depth. Give this researcher one specific topic at a time.",
    "prompt": "You are a dedicated researcher. Conduct thorough research and provide a detailed answer to the user's question. Use the internet_search tool to find current information.",
    "tools": ["internet_search"],
}

critique_sub_agent = {
    "name": "critique-agent",
    "description": "Used to critique and improve research reports.",
    "prompt": "You are an expert editor. Review research reports for accuracy, completeness, and clarity. Provide constructive feedback and suggestions for improvement.",
}

# Main agent instructions
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and write detailed reports.

Use the research-agent to investigate specific topics. Each research-agent call should focus on one specific aspect.

After gathering information, you can use the critique-agent to review and improve your work.

Use the internet_search tool to find current, accurate information on any topic.

When you have enough information, provide a comprehensive answer to the user's question."""

async def main():
    """Run the MCP-integrated research agent"""

    # Check if TAVILY_API_KEY is set
    if not os.environ.get("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY environment variable is not set.")
        print("Please get an API key from https://app.tavily.com/ and set it as:")
        print("export TAVILY_API_KEY=your_api_key_here")
        return

    # Sample research question
    try:
        question = input("Enter a research question (or press Enter for sample): ").strip()
        if not question:
            question = "What are the latest developments in AI agents and autonomous systems?"
    except EOFError:
        question = "What are the latest developments in AI agents and autonomous systems?"

    print(f"\n🔍 Researching: {question}")
    print("=" * 60)

    try:
        # Initialize MCP tools
        search_tool = await initialize_mcp()

        # Create agent with MCP tools
        print("🤖 Creating research agent...")
        agent = async_create_deep_agent(
            tools=[search_tool],
            instructions=research_instructions,
            subagents=[research_sub_agent, critique_sub_agent],
        ).with_config({"recursion_limit": 100})  # Reduced for demo

        # Run the research
        print("📚 Starting research...")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": question}]
        })

        print("\n📋 Research Complete!")
        print("=" * 60)

        # Display results
        if result.get("messages"):
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content') and final_message.content:
                print(f"\n💬 Research Results:\n{final_message.content}")

        # Display any files created
        if "files" in result and result["files"]:
            print("\n📁 Files created:")
            for filename, content in result["files"].items():
                print(f"\n--- {filename} ---")
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 40)

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Make sure your TAVILY_API_KEY is valid and you have internet connectivity.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 DeepAgents Research Agent with MCP Integration")
    print("=" * 60)
    asyncio.run(main())