"""DeepAgents & MCP Integration for Advanced RAG Systems.

A production-ready integration of LangChain's DeepAgents framework with
Model Context Protocol (MCP) for sophisticated multi-strategy retrieval
and evaluation systems.
"""

__version__ = "1.0.0"
__author__ = "DeepAgents Team"
__email__ = "team@deepagents.dev"

# Conditional imports to prevent cascade failures during testing
__all__ = ["__version__"]

try:
    from .retrievers import RetrieverFactory
    __all__.append("RetrieverFactory")
except ImportError:
    pass

try:
    from .agent import create_research_agent
    __all__.append("create_research_agent")
except ImportError:
    pass

try:
    from .mcp import MCPServer
    __all__.append("MCPServer")
except ImportError:
    pass