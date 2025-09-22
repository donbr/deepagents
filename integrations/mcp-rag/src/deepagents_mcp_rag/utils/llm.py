"""LLM utilities for query processing and reranking."""

from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from ..config import get_settings


# Global LLM instance
_llm = None


def get_llm() -> BaseChatModel:
    """Get the global LLM instance.

    Returns:
        LLM instance for text generation
    """
    global _llm

    if _llm is None:
        settings = get_settings()

        _llm = ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.model_name,
            temperature=0.0,  # Deterministic for retrieval tasks
            max_tokens=4096,
        )

    return _llm


def get_llm_for_evaluation() -> BaseChatModel:
    """Get LLM instance optimized for evaluation tasks.

    Returns:
        LLM instance with evaluation-specific configuration
    """
    settings = get_settings()

    return ChatAnthropic(
        api_key=settings.anthropic_api_key,
        model=settings.model_name,
        temperature=0.1,  # Slightly more creative for evaluation
        max_tokens=2048,
    )