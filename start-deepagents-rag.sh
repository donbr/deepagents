#!/usr/bin/env bash
# Wrapper script to start DeepAgents RAG MCP server
# Ensures proper working directory for uv environment

cd integrations/mcp-rag
uv run python minimal_test.py