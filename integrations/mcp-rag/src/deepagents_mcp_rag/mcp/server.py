"""FastMCP server implementation with CQRS pattern for DeepAgents RAG."""

import asyncio
from typing import Dict, Any, Optional
from fastmcp import FastMCP

from .tools import research_deep, evaluate_rag, strategy_compare
from .resources import (
    retrieval_resource,
    strategy_info_resource,
    collection_stats_resource,
    cache_stats_resource,
    performance_metrics_resource
)
from ..config import get_settings
from ..utils.logging import setup_logging, get_logger


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with all tools and resources.

    Returns:
        Configured FastMCP server instance
    """
    # Initialize logging
    setup_logging()
    logger = get_logger(__name__)

    # Create FastMCP instance
    mcp = FastMCP("DeepAgents RAG Server")

    # Register tools (command pattern - full RAG workflows)
    mcp.tool()(research_deep)
    mcp.tool()(evaluate_rag)
    mcp.tool()(strategy_compare)

    # Register resources (query pattern - fast data access)
    mcp.resource("retriever://{strategy}/{query}")(retrieval_resource)
    mcp.resource("strategies://info")(strategy_info_resource)
    mcp.resource("collection://{collection_name}/stats")(collection_stats_resource)
    mcp.resource("cache://stats")(cache_stats_resource)
    mcp.resource("metrics://{strategy}")(performance_metrics_resource)

    logger.info("FastMCP server created with CQRS pattern")
    logger.info("Tools registered: research_deep, evaluate_rag, strategy_compare")
    logger.info("Resources registered: retriever, strategies, collection, cache, metrics")

    return mcp


class MCPServer:
    """Main MCP server class for DeepAgents RAG integration."""

    def __init__(self):
        self.mcp = create_mcp_server()
        self.logger = get_logger(__name__)

    async def run(self, transport: str = "stdio", host: str = "localhost", port: int = 6277):
        """Run the MCP server with specified transport.

        Args:
            transport: Transport type (stdio, http)
            host: Host for HTTP transport
            port: Port for HTTP transport
        """
        settings = get_settings()

        self.logger.info(f"Starting DeepAgents MCP RAG server with {transport} transport")

        if transport == "stdio":
            await self.mcp.run(transport="stdio")

        elif transport == "http":
            await self.mcp.run(
                transport="http",
                host=host,
                port=port,
                path="/mcp"
            )

        else:
            raise ValueError(f"Unsupported transport: {transport}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the MCP server and dependencies.

        Returns:
            Health status of all components
        """
        from ..utils.vector_store import get_qdrant_client, list_collections
        from ..utils.cache import get_cache_client
        from ..retrievers.factory import RetrieverFactory

        health = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }

        # Check vector store
        try:
            qdrant_client = await get_qdrant_client()
            collections = await list_collections()
            health["components"]["vector_store"] = {
                "status": "healthy",
                "collections": len(collections),
                "available_collections": collections
            }
        except Exception as e:
            health["components"]["vector_store"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"

        # Check cache
        try:
            cache = await get_cache_client()
            cache_stats = await cache.get_stats()
            health["components"]["cache"] = {
                "status": "healthy",
                "hit_rate": cache_stats.get("hit_rate", 0),
                "memory_usage": cache_stats.get("used_memory_human", "Unknown")
            }
        except Exception as e:
            health["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"

        # Check retrieval strategies
        try:
            strategies = RetrieverFactory.list_strategies()
            health["components"]["retrievers"] = {
                "status": "healthy",
                "available_strategies": list(strategies.keys()),
                "total_strategies": len(strategies)
            }
        except Exception as e:
            health["components"]["retrievers"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"

        # Check configuration
        try:
            settings = get_settings()
            health["components"]["configuration"] = {
                "status": "healthy",
                "anthropic_api_configured": bool(settings.anthropic_api_key),
                "qdrant_url": settings.qdrant_url,
                "embedding_model": settings.embed_model
            }
        except Exception as e:
            health["components"]["configuration"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "unhealthy"

        return health

    async def get_server_info(self) -> Dict[str, Any]:
        """Get comprehensive server information.

        Returns:
            Server information and capabilities
        """
        from ..retrievers.factory import RetrieverFactory
        from .. import __version__

        return {
            "name": "DeepAgents MCP RAG Server",
            "version": __version__,
            "description": "Multi-strategy RAG system with DeepAgents integration",
            "architecture": "CQRS (Command Query Responsibility Segregation)",
            "capabilities": {
                "tools": [
                    {
                        "name": "research_deep",
                        "description": "Complete RAG pipeline with DeepAgents orchestration",
                        "pattern": "command"
                    },
                    {
                        "name": "evaluate_rag",
                        "description": "RAGAS evaluation of retrieval strategies",
                        "pattern": "command"
                    },
                    {
                        "name": "strategy_compare",
                        "description": "Compare multiple retrieval strategies",
                        "pattern": "command"
                    }
                ],
                "resources": [
                    {
                        "pattern": "retriever://{strategy}/{query}",
                        "description": "Fast document retrieval without synthesis",
                        "performance": "3-5x faster than tools"
                    },
                    {
                        "pattern": "strategies://info",
                        "description": "Information about available retrieval strategies"
                    },
                    {
                        "pattern": "collection://{collection_name}/stats",
                        "description": "Document collection statistics"
                    },
                    {
                        "pattern": "cache://stats",
                        "description": "Cache performance metrics"
                    },
                    {
                        "pattern": "metrics://{strategy}",
                        "description": "Performance metrics for strategies"
                    }
                ]
            },
            "retrieval_strategies": RetrieverFactory.list_strategies(),
            "performance_targets": {
                "raw_retrieval": "<2 seconds",
                "full_research": "<8 seconds",
                "ragas_scores": ">0.85 relevancy, >0.80 precision, >0.90 recall"
            },
            "timestamp": asyncio.get_event_loop().time()
        }


def main():
    """Main entry point for the MCP server - subprocess friendly."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="DeepAgents MCP RAG Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for HTTP transport (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6277,
        help="Port for HTTP transport (default: 6277)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check and exit"
    )
    parser.add_argument(
        "--server-info",
        action="store_true",
        help="Show server information and exit"
    )

    args = parser.parse_args()

    async def run_server():
        # Initialize server
        server = MCPServer()

        # Handle special commands
        if args.health_check:
            health = await server.health_check()
            print(f"Health Status: {health['status']}")
            for component, status in health["components"].items():
                print(f"  {component}: {status['status']}")
                if status["status"] == "unhealthy":
                    print(f"    Error: {status.get('error', 'Unknown')}")
            sys.exit(0 if health["status"] in ["healthy", "degraded"] else 1)

        if args.server_info:
            info = await server.get_server_info()
            print(f"Server: {info['name']} v{info['version']}")
            print(f"Architecture: {info['architecture']}")
            print(f"Available Strategies: {', '.join(info['retrieval_strategies'].keys())}")
            print(f"Tools: {len(info['capabilities']['tools'])}")
            print(f"Resources: {len(info['capabilities']['resources'])}")
            sys.exit(0)

        # Run server
        try:
            await server.run(
                transport=args.transport,
                host=args.host,
                port=args.port
            )
        except KeyboardInterrupt:
            print("\nServer shutdown requested")
        except Exception as e:
            print(f"Server error: {e}")
            sys.exit(1)

    # Use asyncio.run only if we're the main process (subprocess-friendly)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()