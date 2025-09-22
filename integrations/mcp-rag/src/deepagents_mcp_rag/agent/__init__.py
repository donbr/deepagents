"""DeepAgents integration layer."""

from .deep_agent_boot import create_research_agent, create_deep_agent_with_rag
from .prompts import RESEARCH_AGENT_INSTRUCTIONS, RAG_SYSTEM_PROMPT

__all__ = [
    "create_research_agent",
    "create_deep_agent_with_rag",
    "RESEARCH_AGENT_INSTRUCTIONS",
    "RAG_SYSTEM_PROMPT",
]