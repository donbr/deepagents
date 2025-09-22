# DeepAgents & MCP Integration - Claude Code Operator Guide

⚠️ **CRITICAL: Before implementing ANY features, review the [Lessons Learned Documentation](../references/README.md)**

This project implements a sophisticated RAG (Retrieval-Augmented Generation) system using DeepAgents framework with MCP (Model Context Protocol) integration for advanced multi-strategy retrieval and evaluation.

## 📋 Required Reading Before Development

**These documents contain critical lessons from past development - READ THEM FIRST:**
1. **[Retrospective Analysis](../references/retrospective-analysis.md)** - Understand the 85% scope gap from previous work
2. **[Requirements Traceability](../references/requirements-traceability-framework.md)** - Map technical work to business requirements
3. **[MCP Session Management](../references/mcp-session-management-guide.md)** - Avoid connection storm anti-patterns
4. **[Feature Branch Strategy](../references/feature-branch-strategy.md)** - Preserve working functionality
5. **[Process Checklists](../references/process-improvements-checklists.md)** - Follow proven workflows

## Quick Start

### Environment Setup
```bash
# Install dependencies
uv sync

# Start infrastructure services
docker compose -f integrations/mcp-rag/compose.yaml up -d

# Verify MCP server connectivity
claude mcp list
```

### Available Slash Commands
- `/project:research-deep <query>` - Execute deep research with multi-strategy RAG
- `/project:evaluate-rag <strategy>` - Run RAGAS evaluation on specified strategy
- `/project:strategy-compare <query>` - Compare all retrieval strategies for a query

## Development Commands

### Core Operations
- `uv run integrations/mcp-rag/src/mcp/server.py` - Start FastMCP server locally
- `uv run integrations/mcp-rag/scripts/ingest.py` - Ingest documents into vector store
- `uv run pytest integrations/mcp-rag/tests/` - Run test suite
- `docker compose -f integrations/mcp-rag/compose.yaml logs -f` - View service logs

### Evaluation & Testing
- `uv run integrations/mcp-rag/src/eval/harness.py` - Run RAGAS evaluation
- `uv run integrations/mcp-rag/scripts/benchmark.py` - Performance benchmarking
- `uv run integrations/mcp-rag/scripts/golden_set_generate.py` - Generate test dataset

## Architecture Overview

### CQRS Pattern
- **MCP Tools (Commands)**: Full RAG pipeline with synthesis (`research_deep`)
- **MCP Resources (Queries)**: Raw retrieval for 3-5x performance (`retriever://`)

### Retrieval Strategies
1. **BM25**: Keyword search for exact matching
2. **Vector**: Semantic similarity search
3. **Parent Document**: Hierarchical chunking with context
4. **Multi-Query**: Query expansion for comprehensive coverage
5. **Rerank**: LLM-based result reranking for precision
6. **Ensemble**: Combination using Reciprocal Rank Fusion

### Performance Targets
- Raw retrieval: <2 seconds via MCP resources
- Full research cycle: <8 seconds via MCP tools
- RAGAS scores: >0.85 relevancy, >0.80 precision, >0.90 recall
- **Connection Management**: Single persistent session per MCP server (see [MCP Session Guide](../references/mcp-session-management-guide.md))

## Code Style & Patterns

### File Organization
- **Modular design**: Separate retrievers, MCP layer, agent integration, evaluation
- **Factory pattern**: `RetrieverFactory.create(strategy, **kwargs)`
- **Async/await**: All retrieval operations are async for performance
- **Type hints**: Full typing for all functions and classes

### Error Handling
- **Circuit breakers**: Automatic failure detection and recovery
- **Retry logic**: Exponential backoff for transient failures
- **Graceful degradation**: Fallback strategies when primary fails
- **Comprehensive logging**: Structured logs for debugging

### Testing Guidelines
- **Unit tests**: All retrieval strategies and MCP tools
- **Integration tests**: End-to-end workflows with real services
- **Performance tests**: Latency and accuracy benchmarking
- **Golden dataset**: 20+ curated Q/A pairs for consistent evaluation

## Security & Best Practices

### Environment Variables
All sensitive data uses environment variable expansion:
- `OPENAI_API_KEY`: Required for LLM operations
- `QDRANT_URL`: Vector database connection
- `LANGSMITH_API_KEY`: Optional observability
- `PHOENIX_ENDPOINT`: Local tracing endpoint

### Tool Safety
- **Sandboxed execution**: DeepAgents virtual file system
- **Rate limiting**: Configured per tool in MCP server
- **Audit logging**: All operations logged for compliance
- **Permission boundaries**: Restricted to allowed tools list

## Troubleshooting

### MCP Connectivity
```bash
# Debug MCP server issues
claude --mcp-debug

# Test server health
curl http://localhost:6277/health

# Check service dependencies
docker compose -f integrations/mcp-rag/compose.yaml ps
```

### Performance Issues
- **Check caching**: Verify Redis connectivity and hit rates
- **Monitor resources**: CPU/memory usage during retrieval
- **Review logs**: Phoenix traces for bottlenecks
- **Benchmark**: Compare strategies with timing data

### Common Issues
- **API key errors**: Verify environment variables are set
- **Vector store**: Ensure Qdrant is running and accessible
- **Model compatibility**: Some models require structured output handling
- **Token limits**: Large retrievals may exceed context windows

## Observability

### Monitoring Tools
- **Phoenix**: Local development tracing (http://localhost:6006)
- **LangSmith**: Production observability with dataset tracking
- **RAGAS Dashboard**: Quality metrics and evaluation trends
- **Docker logs**: Service-level logging and health status

### Key Metrics
- **Retrieval latency**: P50/P95 response times per strategy
- **Quality scores**: RAGAS metrics trending over time
- **Token usage**: Cost optimization tracking
- **Error rates**: Circuit breaker triggers and fallback usage

## Team Collaboration

### Version Control
- **`.mcp.json`**: Shared MCP server configuration
- **`.claude/`**: Team settings and slash commands
- **Environment**: Use `.env.example` for setup guidance
- **Documentation**: Keep this guide updated with changes

### Onboarding Checklist
1. **READ FIRST**: Review [Retrospective Analysis](../references/retrospective-analysis.md) and [Process Checklists](../references/process-improvements-checklists.md)
2. Clone repository and run `uv sync`
3. Copy `.env.example` to `.env` and configure
4. Start services with `docker compose up -d`
5. Verify MCP connectivity with `claude mcp list`
6. Test slash commands with `/project:research-deep "test query"`
7. **IMPORTANT**: Follow [Feature Branch Strategy](../references/feature-branch-strategy.md) for all development

IMPORTANT: Always run evaluation after making changes to ensure quality doesn't regress. Use `/project:evaluate-rag ensemble` to validate system performance.

## ⚠️ Critical Anti-Patterns to Avoid

**From [MCP Session Management Guide](../references/mcp-session-management-guide.md):**
- **NEVER use** `client.get_tools()` - causes connection storms (20+ connections per query)
- **ALWAYS use** explicit session management with `load_mcp_tools(session)`

**From [Feature Branch Strategy](../references/feature-branch-strategy.md):**
- **NEVER modify** working code directly - use additive development
- **ALWAYS preserve** existing functionality while adding new features

**From [Requirements Analysis](../references/retrospective-analysis.md):**
- **NEVER start coding** before reading requirements documentation
- **ALWAYS validate** scope understanding with stakeholders