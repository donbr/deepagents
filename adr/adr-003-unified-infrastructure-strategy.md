# ADR-003: Unified Infrastructure Strategy for Three-Repository Integration

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

We have three repositories with overlapping infrastructure requirements:

1. **deepagents**: Main framework with planned MCP-RAG integration
2. **adv-rag**: Complete MCP server + RAG functionality (95% implemented)
3. **rag-eval-foundations**: RAGAS evaluation pipeline (95% implemented)

### Current Infrastructure Conflicts

| Service | deepagents | adv-rag | rag-eval-foundations | Status |
|---------|------------|---------|---------------------|---------|
| Phoenix | 6006:6006, 4317:4317 | 6006:6006, 4317:4317 | 6006:6006, 4317:4317 | ⚠️ **PORT CONFLICT** |
| PostgreSQL | 5432:5432 | ❌ None | 6024:5432 | ⚠️ **INCONSISTENT** |
| Qdrant | 6333:6333 | 6333:6333 | ❌ None | ⚠️ **PARTIAL** |
| Redis | 6379:6379 | 6379:6379 | ❌ None | ⚠️ **PARTIAL** |

### Integration Requirements
- DeepAgents needs to connect to adv-rag MCP server
- rag-eval-foundations needs to evaluate DeepAgents→adv-rag performance
- All three need shared Phoenix observability for end-to-end tracing
- Avoid duplicate services and resource waste

## Decision

### Selected Strategy: **Centralized Infrastructure with Service Discovery**

We will establish **rag-eval-foundations** as the infrastructure host repository because:
- It has the most complete Docker configuration with health checks
- Already configured for non-conflicting ports
- Has comprehensive evaluation framework
- Natural fit as the orchestration/monitoring hub

### Implementation Plan

#### Phase 1: Infrastructure Consolidation
1. **Designate rag-eval-foundations as infrastructure host**
   - All Docker services run from rag-eval-foundations
   - Other repositories connect to centralized services
   - Unified Phoenix instance for cross-project observability

2. **Service Port Mapping Strategy**
   ```yaml
   # Centralized in rag-eval-foundations/docker-compose.yml
   services:
     postgres:     # Primary DB for evaluation data
       ports: ["6024:5432"]
     qdrant:       # Vector DB for RAG functionality
       ports: ["6333:6333", "6334:6334"]
     redis:        # Caching for all three projects
       ports: ["6379:6379"]
     phoenix:      # Unified observability
       ports: ["6006:6006", "4317:4317"]
   ```

3. **Cross-Repository Service Discovery**
   ```bash
   # Each repository includes infrastructure helper
   scripts/infrastructure/check-shared-services.sh
   scripts/infrastructure/connect-to-shared-infrastructure.sh
   ```

#### Phase 2: Service Integration Contracts
1. **API Contracts Definition**
   - adv-rag MCP server: stdio and HTTP interfaces
   - DeepAgents client: MCP connection patterns
   - rag-eval-foundations: evaluation API endpoints

2. **Health Check Framework**
   ```bash
   # Unified health checks across all three repos
   curl http://localhost:6024/health  # PostgreSQL via pg_isready
   curl http://localhost:6333/health  # Qdrant vector DB
   curl http://localhost:6379         # Redis cache (PING)
   curl http://localhost:6006/health  # Phoenix observability
   ```

3. **Environment Configuration Strategy**
   ```bash
   # Shared environment variables
   export SHARED_POSTGRES_URL="postgresql://langchain:langchain@localhost:6024/langchain"
   export SHARED_QDRANT_URL="http://localhost:6333"
   export SHARED_REDIS_URL="redis://localhost:6379"
   export SHARED_PHOENIX_ENDPOINT="http://localhost:6006"
   ```

#### Phase 3: Cross-Repository Integration
1. **DeepAgents → adv-rag MCP Client**
   - Implement `langchain-mcp-adapters` client in DeepAgents
   - Connect to adv-rag stdio MCP server
   - Use explicit session management (avoid connection storms)

2. **rag-eval-foundations → End-to-End Evaluation**
   - Extend RAGAS pipeline to evaluate DeepAgents workflows
   - Add performance benchmarking for <2s/<8s targets
   - Phoenix tracing integration for complete pipeline visibility

3. **Unified Observability Strategy**
   - Single Phoenix instance captures all three project traces
   - Project-specific tags for filtering: `project=deepagents|adv-rag|rag-eval`
   - Cross-project experiment comparison capabilities

## Consequences

### ✅ **Positive**
- **Eliminates port conflicts**: No more service startup failures
- **Reduces resource usage**: Single set of infrastructure services
- **Enables cross-project tracing**: Complete end-to-end observability
- **Simplifies development**: One infrastructure to manage
- **Facilitates integration testing**: All components in known locations

### ⚠️ **Risks & Mitigations**
- **Single point of failure**: Infrastructure dependency
  - *Mitigation*: Comprehensive health checks and service restart policies
- **Cross-project coupling**: Changes affect multiple repositories
  - *Mitigation*: API contracts and versioned interfaces
- **Development complexity**: Need to start infrastructure before work
  - *Mitigation*: Automated startup scripts and clear documentation

### 📋 **Action Items**
1. **Infrastructure consolidation** (Week 1)
   - [ ] Update rag-eval-foundations docker-compose.yml with all services
   - [ ] Create service discovery scripts for all three repos
   - [ ] Document unified environment configuration

2. **API contracts** (Week 1)
   - [ ] Define MCP client interface for DeepAgents
   - [ ] Specify evaluation API for cross-repo testing
   - [ ] Create health check framework

3. **Integration implementation** (Week 2)
   - [ ] Implement DeepAgents MCP client
   - [ ] Extend rag-eval pipeline for end-to-end testing
   - [ ] Configure unified Phoenix observability

4. **Testing & validation** (Week 2)
   - [ ] End-to-end performance testing
   - [ ] Cross-project observability validation
   - [ ] Integration test suite for all three repos

## Implementation Notes

### Service Priority Order
1. **rag-eval-foundations infrastructure**: PostgreSQL, Phoenix (core services)
2. **adv-rag requirements**: Qdrant, Redis (RAG-specific services)
3. **deepagents integration**: MCP client, evaluation hooks

### Performance Targets
- **Raw retrieval**: <2 seconds via MCP resources
- **Full research cycle**: <8 seconds via MCP tools
- **End-to-end evaluation**: <30 seconds for complete pipeline
- **Cross-project tracing**: <100ms overhead per trace

### Monitoring & Observability
- **Phoenix project tags**: Distinguish traces by source repository
- **Performance dashboards**: Cross-project metrics and comparisons
- **Health monitoring**: Automated service health checks across all repos

## References
- [Requirements Traceability Matrix](./requirements-traceability-framework.md)
- [MCP Session Management Guide](./mcp-session-management-guide.md)
- [Feature Branch Strategy](./feature-branch-strategy.md)
- adv-rag repository: Complete MCP server implementation
- rag-eval-foundations repository: RAGAS evaluation pipeline