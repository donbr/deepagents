# ADR-003: DeepAgents MCP-RAG Integration Architecture Assessment

**Date:** 2025-01-21
**Status:** Proposed
**Deciders:** Engineering Team
**Consulted:** Context7, FastMCP Documentation, LangGraph Documentation
**Informed:** Project Stakeholders

## Context

### Background
The DeepAgents project requires a sophisticated MCP-based retrieval and evaluation platform to meet the requirements specified in `references/INSTRUCTIONS.md`. Previous retrospective analysis revealed only 15% of required functionality was delivered, with significant gaps between business requirements and technical implementation.

Research using MCP tools (Context7, AI-docs-llms, Tavily) has provided comprehensive understanding of:
- DeepAgents architecture and MCP integration patterns
- FastMCP 2.0 server implementation with CQRS pattern
- LangGraph multi-agent orchestration capabilities
- Session management anti-patterns and best practices

### Constraints
- Must work with existing DeepAgents framework in `src/deepagents/`
- Must integrate with FastMCP 2.0 server architecture in `integrations/mcp-rag/`
- Cannot modify working `research_agent.py` (additive development only)
- Must support docker-compose infrastructure (Qdrant, Redis, PostgreSQL, Phoenix)
- Must use proper MCP session management to avoid connection storms
- Must deliver all 6 retrieval strategies and RAGAS evaluation framework

### Requirements
Based on `references/INSTRUCTIONS.md`:
1. **Multi-Strategy Retrieval**: BM25, vector, parent-doc, multi-query, rerank, ensemble
2. **RAGAS Evaluation Framework**: Answer relevancy, context precision/recall, faithfulness
3. **MCP Dual Interface**: Tools (commands) + Resources (queries) following CQRS pattern
4. **Performance Targets**: <2s raw retrieval, <8s full answer
5. **DeepAgents Integration**: Planning, sub-agents, file system, detailed prompts
6. **Observability**: Phoenix/LangSmith with per-step spans
7. **Local-First**: Docker/WSL2 runnable with health checks

## Decision

### What We Will Do
Implement a comprehensive DeepAgents MCP-RAG integration using additive development patterns that preserves existing functionality while delivering all required capabilities.

**Architecture Components:**
1. **Multi-Strategy RetrieverFactory** with pluggable retrieval implementations
2. **DeepAgents Integration** using proper sub-agent orchestration
3. **FastMCP Server** with CQRS pattern (Tools + Resources)
4. **Session Management** using explicit lifecycle pattern
5. **RAGAS Evaluation** pipeline with golden dataset
6. **Observability Stack** with Phoenix tracing and metrics

### What We Will Not Do
- We will not modify working `research_agent.py` - will create parallel implementation
- We will not use `client.get_tools()` pattern that creates connection storms
- We will not implement without requirements traceability validation
- We will not compromise on performance targets or quality metrics

## Rationale

### Pros of Chosen Approach
- **Requirements Compliance**: Delivers 100% of INSTRUCTIONS.md scope vs 15% previously
- **Architecture Maturity**: Follows established patterns from Context7 research
- **Performance Optimized**: CQRS pattern enables <2s raw retrieval targets
- **Integration Robust**: Proper session management eliminates connection storms
- **Development Safe**: Additive approach preserves working baseline
- **Quality Assured**: RAGAS framework provides measurable evaluation

### Cons of Chosen Approach
- **Implementation Complexity**: Requires sophisticated multi-component integration
- **Learning Curve**: Team needs to understand DeepAgents + FastMCP + RAGAS
- **Testing Overhead**: End-to-end system requires comprehensive test coverage
- **Infrastructure Dependencies**: Docker services and observability stack required

### Alternatives Considered
1. **Simple Tavily Integration Enhancement** - Rejected as doesn't meet requirements scope
2. **Direct Modification of Existing Code** - Rejected due to feature branch strategy
3. **Gradual Incremental Development** - Rejected as requirements are interconnected
4. **Third-Party RAG Platform** - Rejected as doesn't provide DeepAgents integration

## Consequences

### Positive Consequences
- **Scope Alignment**: Delivery matches business requirements completely
- **Performance Achievement**: Meets <2s/<8s latency targets
- **Quality Metrics**: RAGAS scores provide objective evaluation
- **Maintainable Architecture**: Clean separation of concerns with CQRS
- **Extensible Framework**: Pluggable retrievers enable future strategies
- **Operational Readiness**: Observability and monitoring built-in

### Negative Consequences
- **Development Time**: Complex integration requires significant implementation
- **System Complexity**: Multi-service architecture requires operational expertise
- **Resource Requirements**: Docker infrastructure consumes development resources
- **Learning Investment**: Team needs training on multiple technologies

### Risks
- **Integration Complexity** - Mitigated by incremental validation and testing
- **Performance Bottlenecks** - Mitigated by performance monitoring and optimization
- **Service Dependencies** - Mitigated by health checks and graceful degradation
- **Scope Creep** - Mitigated by requirements traceability matrix

## Implementation Notes

### Technical Details

**DeepAgents Integration Pattern:**
```python
from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# Proper session management (avoid connection storms)
mcp_session_context = mcp_client.session("deepagents-rag")
session = await mcp_session_context.__aenter__()
tools = await load_mcp_tools(session)

# Create agent with retrieval sub-agents
agent = create_deep_agent(
    tools=tools,
    instructions=research_instructions,
    subagents=[research_subagent, critique_subagent],
    model="claude-sonnet-4-20250514"
)
```

**CQRS FastMCP Server Pattern:**
```python
# Commands (full RAG pipeline)
@mcp.tool()
async def research_deep(question: str, strategy: str = "auto") -> Dict[str, Any]:
    # DeepAgents orchestration + synthesis + evaluation

# Queries (fast raw retrieval)
@mcp.resource("retriever://{strategy}/{query}")
async def retrieval_resource(strategy: str, query: str) -> str:
    # Direct retriever access for performance
```

### Dependencies
- `deepagents` package with sub-agent support
- `fastmcp>=2.12.3` for server implementation
- `langchain-mcp-adapters>=0.1.0` for session management
- `ragas` for evaluation framework
- Docker services: Qdrant, Redis, PostgreSQL, Phoenix
- Observability: Phoenix tracing, LangSmith integration

### Timeline
- **Day 1**: ADR creation, requirements traceability
- **Day 2**: Infrastructure validation, implementation audit
- **Days 3-4**: Core architecture implementation
- **Day 5**: Testing, documentation, production readiness

## Validation

### Success Criteria
- **All 6 retrieval strategies** implemented and functional
- **RAGAS evaluation** producing quality scores for all strategies
- **Performance targets met**: <2s raw retrieval, <8s full research
- **MCP dual interface** working (Tools + Resources)
- **DeepAgents integration** with sub-agent orchestration
- **Local deployment** operational via docker-compose
- **Zero regressions** in existing research_agent.py functionality

### Monitoring
- **Performance Metrics**: Phoenix tracing with per-step latency
- **Quality Metrics**: RAGAS scores trending over time
- **System Health**: Docker service monitoring and health checks
- **Integration Health**: MCP session lifecycle and connection monitoring
- **Usage Patterns**: Claude Code slash command usage analytics

### Review Date
2025-02-21 - Comprehensive architecture review and lessons learned

## References

- [Project Requirements](../INSTRUCTIONS.md)
- [Retrospective Analysis](../retrospective-analysis.md)
- [MCP Session Management Guide](../mcp-session-management-guide.md)
- [Feature Branch Strategy](../feature-branch-strategy.md)
- [DeepAgents Context7 Documentation](/langchain-ai/deepagents)
- [FastMCP Documentation](https://gofastmcp.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---
*This ADR supersedes: None*
*This ADR is superseded by: None*