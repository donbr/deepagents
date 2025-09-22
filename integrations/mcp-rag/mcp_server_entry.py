#!/usr/bin/env python3
# /// script
# dependencies = [
#   "fastmcp>=2.12.0",
#   "qdrant-client>=1.7.0",
#   "sentence-transformers>=2.2.0",
#   "anthropic>=0.25.0",
#   "redis>=4.5.0",
#   "psycopg2-binary>=2.9.0",
#   "arize-phoenix>=4.0.0",
#   "langsmith>=0.1.0",
# ]
# ///
"""
MCP Server Entry Point for Claude Code integration.

This is specifically designed to avoid asyncio event loop conflicts
when running as a subprocess from Claude Code.
"""

import sys
import os
import asyncio

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from deepagents_mcp_rag.mcp.server import create_mcp_server
from deepagents_mcp_rag.utils.logging import setup_logging, get_logger


async def run_mcp_server():
    """Run the MCP server in a clean asyncio context."""
    setup_logging()
    logger = get_logger(__name__)

    try:
        mcp = create_mcp_server()
        logger.info("Starting MCP server with stdio transport")
        await mcp.run_async(transport="stdio")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        raise


def main():
    """Main entry point - creates fresh asyncio event loop."""
    # Ensure we have a clean event loop
    try:
        loop = asyncio.get_running_loop()
        # If we get here, there's already a loop running
        print("Error: asyncio event loop already running", file=sys.stderr)
        sys.exit(1)
    except RuntimeError:
        # Good - no loop is running
        pass

    # Create and run a new event loop
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()