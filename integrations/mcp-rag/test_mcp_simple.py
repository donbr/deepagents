#!/usr/bin/env python3
"""Simple MCP server for testing Claude Code integration."""

import asyncio
from fastmcp import FastMCP


def create_simple_mcp():
    """Create a minimal MCP server for testing."""
    mcp = FastMCP("Test DeepAgents RAG Server")

    @mcp.tool()
    def test_tool(message: str = "Hello from DeepAgents RAG!") -> str:
        """Simple test tool to verify MCP connectivity.

        Args:
            message: Message to echo back

        Returns:
            Echo of the message with server info
        """
        return f"DeepAgents MCP RAG Server received: {message}"

    @mcp.resource("test://echo/{text}")
    def test_resource(text: str) -> str:
        """Simple test resource.

        Args:
            text: Text to echo

        Returns:
            Echo of the text
        """
        return f"Resource echo: {text}"

    return mcp


async def main():
    """Main entry point."""
    mcp = create_simple_mcp()
    await mcp.run(transport="stdio")


if __name__ == "__main__":
    asyncio.run(main())