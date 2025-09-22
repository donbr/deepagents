# ADR-004: Repository Separation Pattern

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

The DeepAgents ecosystem consists of three repositories that were developed independently but must integrate to provide a comprehensive RAG-enabled agent system. Analysis reveals that each repository has evolved to serve distinct, non-overlapping capabilities that form a natural architectural separation.

### Repository Analysis

#### DeepAgents Repository (~90% Complete)
**Location**: `/home/donbr/sept2025/deepagents/`
**Role**: Agent orchestration and workflow management framework

**Core Capabilities**:
- **Planning System**: `write_todos` tool for structured task breakdown
- **Sub-agent Orchestration**: Dynamic sub-agent creation and management via `task` tool
- **Virtual File System**: Isolated file operations within LangGraph state
- **LangGraph Integration**: State management and conversation flow control
- **Human-in-the-Loop**: Approval workflows for tool execution

**Architecture Pattern**: Planning-first approach with virtual file system isolation
**Maturity**: Production-ready framework with comprehensive documentation

#### adv-rag Repository (~95% Complete)
**Location**: `/home/donbr/sept2025/deepagents/repos/adv-rag/`
**Role**: Production RAG system with dual MCP interfaces

**Core Capabilities**:
- **6 Retrieval Strategies**: naive, semantic, bm25, compression, multiquery, ensemble
- **CQRS MCP Pattern**: Tools (commands) and Resources (queries) via MCP
- **Vector Storage**: Qdrant integration with collection management
- **Caching Layer**: Redis integration for performance optimization
- **Phoenix Telemetry**: Comprehensive observability and tracing

**Architecture Pattern**: Tier-based system with immutable core layers
**Maturity**: Fully operational with validated performance (<30s retrieval)

#### rag-eval-foundations Repository (~95% Complete)
**Location**: `/home/donbr/sept2025/deepagents/repos/rag-eval-foundations/`
**Role**: RAGAS evaluation pipeline and infrastructure orchestration

**Core Capabilities**:
- **3-Stage Evaluation**: Infrastructure → Golden Dataset → Automated Metrics
- **RAGAS Integration**: Answer relevancy, context precision/recall, faithfulness
- **PostgreSQL Backend**: Evaluation data storage with pgvector support
- **Infrastructure Hosting**: Docker services for entire ecosystem
- **Phoenix Observability**: Unified telemetry platform

**Architecture Pattern**: Infrastructure centralization with comprehensive evaluation
**Maturity**: Complete pipeline with 269 PDF documents and 6 strategy validation

## Decision

### Repository Responsibility Allocation

We will maintain **strict separation of concerns** with each repository owning distinct capabilities:

#### **DeepAgents** - Agent Orchestration Domain
**Responsibilities**:
- Agent lifecycle management and sub-agent spawning
- Planning workflow orchestration (`write_todos` → execution cycle)
- Human-in-the-loop approval workflows
- Virtual file system management for multi-agent scenarios
- Integration with external MCP services as **CLIENT**

**Boundaries**:
- ❌ **Does NOT implement**: RAG algorithms, evaluation metrics, infrastructure
- ✅ **Integrates with**: adv-rag via MCP client, rag-eval-foundations for evaluation

#### **adv-rag** - RAG Service Domain
**Responsibilities**:
- RAG algorithm implementation and optimization
- Vector storage and retrieval operations
- MCP server providing Tools (commands) and Resources (queries)
- Performance optimization and caching strategies
- RAG-specific observability and metrics

**Boundaries**:
- ❌ **Does NOT implement**: Agent orchestration, evaluation frameworks, infrastructure
- ✅ **Provides services to**: DeepAgents via MCP, rag-eval-foundations for evaluation

#### **rag-eval-foundations** - Evaluation & Infrastructure Domain
**Responsibilities**:
- RAGAS evaluation pipeline and metrics calculation
- Infrastructure orchestration (Docker, services, networking)
- PostgreSQL backend for evaluation data persistence
- Cross-repository performance measurement
- Unified observability platform (Phoenix hosting)

**Boundaries**:
- ❌ **Does NOT implement**: Agent logic, RAG algorithms
- ✅ **Supports**: Infrastructure for both DeepAgents and adv-rag, evaluation of entire ecosystem

## Implementation Patterns

### **1. Interface-Based Integration**
```yaml
# Integration flow
DeepAgents (Client) → MCP Protocol → adv-rag (Server)
         ↓
   rag-eval-foundations (Infrastructure + Evaluation)
```

**Benefits**:
- Clear API boundaries prevent tight coupling
- MCP protocol ensures standard interface contracts
- Each repository can evolve independently

### **2. Service Discovery Pattern**
```bash
# Each repository includes infrastructure helpers
./scripts/infrastructure/connect-to-shared-infrastructure.sh
```

**Implementation**:
- Automated health checks for cross-repository dependencies
- Environment variable guidance for service endpoints
- Clear documentation of service requirements

### **3. No Functionality Duplication**
**Enforced Boundaries**:
- DeepAgents ❌ cannot implement RAG logic → must use adv-rag MCP
- adv-rag ❌ cannot implement agents → provides services only
- rag-eval-foundations ❌ cannot implement business logic → infrastructure + evaluation only

### **4. Data Flow Separation**
```mermaid
graph LR
    A[DeepAgents State] → B[MCP Protocol] → C[adv-rag Collections]
    C → D[rag-eval-foundations PostgreSQL]
    E[Phoenix Tracing] ← F[All Repositories]
```

**Patterns**:
- DeepAgents: Virtual file system for agent-specific data
- adv-rag: Qdrant collections for vector data, Redis for caching
- rag-eval-foundations: PostgreSQL for evaluation metrics

## Architectural Benefits

### **1. Clear Ownership and Accountability**
- Each team/maintainer has clear domain responsibility
- Bug reports and feature requests route to correct repository
- Performance optimization focused on domain expertise

### **2. Independent Evolution**
- Repositories can be updated without affecting others (within interface contracts)
- Technology stack decisions isolated to domain requirements
- Testing and deployment can be independent

### **3. Composable Architecture**
- New repositories can integrate via standard patterns
- Functionality can be mixed and matched based on requirements
- Clear upgrade/replacement paths for components

### **4. Reduced Complexity**
- Developers only need to understand their domain
- Debugging isolated to relevant repository
- Documentation and onboarding scoped to specific concerns

## Integration Constraints

### **1. Interface Contract Compliance**
- **MCP Protocol**: All integrations must use standard MCP patterns
- **Service Discovery**: Health checks and service availability detection required
- **Error Handling**: Graceful degradation when services unavailable

### **2. Data Consistency Requirements**
- **Model Pinning**: Consistent models across repositories (see ADR-007)
- **Schema Alignment**: Compatible data formats where integration occurs
- **Versioning**: API versioning strategy for breaking changes

### **3. Performance Boundaries**
- **Raw Retrieval**: <2s target (adv-rag responsibility)
- **Full Workflows**: <8s target (cross-repository coordination)
- **Evaluation Cycles**: Reasonable batch processing times

## Monitoring and Compliance

### **Repository Health Metrics**
```bash
# DeepAgents health
python -c "import deepagents; print('✅ Framework ready')"

# adv-rag health
curl http://localhost:8000/health

# rag-eval-foundations health
docker ps --filter 'label=project=deepagents-ecosystem'
```

### **Integration Validation**
- **MCP Connectivity**: DeepAgents can reach adv-rag MCP server
- **Service Discovery**: All repositories detect shared infrastructure
- **End-to-end Testing**: Complete workflows execute successfully

### **Boundary Enforcement**
- **Code Reviews**: Verify changes stay within repository domain
- **Architecture Reviews**: Validate new features don't violate separation
- **Documentation Updates**: Ensure patterns remain current

## Consequences

### ✅ **Positive Outcomes**
- **Clear Development Boundaries**: Teams know exactly what to work on
- **Reduced Integration Complexity**: Standard patterns for all integrations
- **Independent Scaling**: Each domain can optimize for its specific requirements
- **Maintainability**: Bug fixes and features isolated to relevant repositories

### ⚠️ **Risks and Mitigations**
- **Integration Overhead**: Additional complexity in cross-repository workflows
  - *Mitigation*: Standardized MCP patterns and health checks
- **Interface Changes**: Breaking changes affect multiple repositories
  - *Mitigation*: API versioning and backward compatibility strategies
- **Coordination Complexity**: Features spanning repositories require coordination
  - *Mitigation*: Clear ownership model and communication protocols

### 📋 **Action Items**
1. **Document Integration Contracts**: Formal API specifications between repositories
2. **Implement Health Checks**: Automated validation of cross-repository dependencies
3. **Create Migration Guides**: When changes affect multiple repositories
4. **Establish Change Management**: Process for coordinated updates

## Implementation Examples

### **DeepAgents Integration Pattern**
```python
# DeepAgents uses MCP client to access adv-rag
from langchain_mcp_adapters import MultiServerMCPClient

async def create_research_agent():
    mcp_client = MultiServerMCPClient()
    # Connect to adv-rag MCP server
    tools = await mcp_client.get_tools("adv-rag")
    # Create agent with RAG tools
    return create_deep_agent(tools=tools)
```

### **adv-rag Service Pattern**
```python
# adv-rag provides MCP tools, does not orchestrate agents
@app.post("/invoke/semantic_retriever")
async def semantic_retriever(request: RetrievalRequest):
    # Pure RAG service implementation
    return await retrieval_chain.ainvoke(request.question)
```

### **rag-eval-foundations Evaluation Pattern**
```python
# Evaluates DeepAgents + adv-rag integration
def evaluate_agent_pipeline():
    # Infrastructure provided, evaluation of ecosystem
    agent = create_deepagents_with_rag()
    metrics = run_ragas_evaluation(agent)
    store_results_in_postgresql(metrics)
```

## References
- [Repository Integration Guide](./unified-infrastructure-implementation-summary.md)
- [MCP Session Management Guide](./mcp-session-management-guide.md)
- [Feature Branch Strategy](./feature-branch-strategy.md)
- [Requirements Traceability Framework](./requirements-traceability-framework.md)

---

**Key Principle**: Each repository owns a distinct domain with clear boundaries. Integration occurs through well-defined interfaces, never through direct code sharing or functionality duplication.