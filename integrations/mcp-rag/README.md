# DeepAgents MCP RAG Integration

A production-ready Model Context Protocol (MCP) server that provides advanced Retrieval-Augmented Generation (RAG) capabilities for Claude Code. This integration combines multiple retrieval strategies with comprehensive evaluation frameworks to deliver optimal information retrieval performance.

## 🚀 Features

- **CQRS Pattern Implementation**: Separate command (full RAG) and query (raw retrieval) interfaces
- **Multi-Strategy Retrieval**: 6 configurable strategies (BM25, vector, parent-doc, multi-query, rerank, ensemble)
- **RAGAS Evaluation Framework**: Comprehensive quality assessment with answer relevancy, precision, recall, faithfulness
- **FastMCP 2.0 Server**: High-performance MCP server with stdio/HTTP transports and health monitoring
- **DeepAgents Integration**: Sophisticated agent orchestration with virtual file system
- **Production Observability**: Phoenix tracing, Redis caching, PostgreSQL metrics storage
- **Team Collaboration**: Version-controlled configuration with environment variable expansion

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Claude Code with MCP support
- Required API keys (see Configuration)

### Installation

1. **Clone and install dependencies:**
```bash
cd integrations/mcp-rag
uv sync --dev
```

2. **Start infrastructure services:**
```bash
docker compose up -d qdrant redis postgres phoenix
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

4. **Run the MCP server:**
```bash
uv run python -m deepagents_mcp_rag.mcp.server --transport stdio
```

### Claude Code Integration

The MCP server is automatically configured via the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "deepagents-rag": {
      "command": "uv",
      "args": ["run", "python", "-m", "deepagents_mcp_rag.mcp.server"],
      "cwd": "integrations/mcp-rag",
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

## 🏗️ Architecture

### CQRS Pattern Implementation

The system follows Command Query Responsibility Segregation (CQRS):

- **Commands (Tools)**: Full RAG workflows with processing overhead
- **Queries (Resources)**: Fast, read-only document retrieval

### Retrieval Strategies

| Strategy | Latency | Use Case | Strengths |
|----------|---------|-----------|-----------||
| **BM25** | ~5ms | Exact keyword matching | Fast, interpretable |
| **Vector** | ~20ms | Semantic similarity | Context understanding |
| **Parent-Doc** | ~50ms | Context preservation | Full document context |
| **Multi-Query** | ~100ms | Comprehensive coverage | Multiple perspectives |
| **Rerank** | ~200ms | Precision optimization | Relevance ranking |
| **Ensemble** | ~180ms | Balanced performance | Best F1 score |

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │───▶│   MCP Server    │───▶│  DeepAgents     │
│                 │    │   (FastMCP)     │    │   Framework     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────┐
        │                Infrastructure                        │
        ├─────────────┬─────────────┬─────────────┬───────────┤
        │   Qdrant    │    Redis    │ PostgreSQL  │  Phoenix  │
        │  (Vectors)  │  (Cache)    │ (Metadata)  │ (Observ.) │
        └─────────────┴─────────────┴─────────────┴───────────┘
```

## Usage

### Claude Code Slash Commands

```bash
# Deep research with strategy auto-selection
/project:research-deep "What are the benefits of parent document retrieval?"

# Comprehensive evaluation
/project:evaluate-rag ensemble

# Strategy performance comparison
/project:strategy-compare "How does multi-query expansion improve recall?"
```

### Programmatic API

```python
from deepagents_mcp_rag.retrievers import RetrieverFactory
from deepagents_mcp_rag.agent import create_research_agent

# Create retriever
retriever = RetrieverFactory.create("ensemble", k=5)
docs = await retriever.retrieve("query")

# Create research agent
agent = create_research_agent()
result = await agent.research("complex question")
```

### MCP Integration

```python
from deepagents_mcp_rag.mcp import MCPServer

# Start MCP server
server = MCPServer()
await server.run(transport="stdio")
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-cloud-key

# Observability (Optional)
LANGSMITH_API_KEY=ls_your-key-here
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:4317

# Performance Tuning
MAX_RETRIEVAL_RESULTS=10
CACHE_TTL_SECONDS=3600
```

### Strategy Selection

```python
# Automatic selection based on query characteristics
strategy = "auto"  # Recommended default

# Manual selection
strategy = "bm25"      # Best for exact terms
strategy = "vector"    # Best for semantic similarity
strategy = "ensemble"  # Best overall performance
```

## Development

### Testing

```bash
# Run test suite
uv run pytest

# Integration tests with services
docker compose up -d
uv run pytest -m integration

# Performance benchmarking
uv run python scripts/benchmark.py
```

### Evaluation

```bash
# Run RAGAS evaluation
uv run python src/eval/harness.py

# Generate golden dataset
uv run python scripts/golden_set_generate.py

# Compare strategies
uv run python scripts/strategy_comparison.py
```

### Code Quality

```bash
# Format code
uv run black src tests
uv run isort src tests

# Lint
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Monitoring

### Local Development
- **Phoenix UI**: http://localhost:6006 (tracing and debugging)
- **Qdrant Dashboard**: http://localhost:6333/dashboard (vector store)
- **Redis Insight**: http://localhost:8001 (cache monitoring)

### Production
- **LangSmith**: Dataset tracking and evaluation
- **RAGAS Dashboard**: Quality metrics and trends
- **OpenTelemetry**: Distributed tracing and metrics

## Troubleshooting

### Common Issues

**MCP Connectivity**:
```bash
# Debug server issues
claude --mcp-debug

# Check server health
curl http://localhost:6277/health
```

**Performance Issues**:
```bash
# Monitor resource usage
docker compose logs -f

# Check cache hit rates
redis-cli info stats
```

**Quality Issues**:
```bash
# Run evaluation
uv run python src/eval/harness.py --verbose

# Check strategy performance
uv run python scripts/benchmark.py --strategy all
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run quality checks (`uv run pytest && uv run ruff check`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Create Pull Request

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Support

- **Documentation**: [Project Wiki](../../docs/)
- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)