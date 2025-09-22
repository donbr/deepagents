# ADR-006: Tier-Based Architecture Constraints

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

The adv-rag repository implements a sophisticated **tier-based architecture** with strict modification rules that ensure system integrity and maintain public contracts. This architecture was discovered to be **immutable by design** with specific tiers that can never be modified and others that serve as safe extension points.

### Architecture Analysis

**Repository**: `/home/donbr/sept2025/deepagents/repos/adv-rag/`
**System Version**: Advanced RAG with CQRS MCP Resources v2.5
**Status**: ✅ FULLY OPERATIONAL - All components tested and working
**Key Constraint**: 5-tier hierarchy with immutable core layers

### Tier Hierarchy (From adv-rag/CLAUDE.md)

#### **Tier 1: Project Core** (IMMUTABLE)
**Contents**: Model pinning, import conventions, configuration
**Location**: `src/core/settings.py`, `src/integrations/llm_models.py`
**Rule**: ❌ **NEVER MODIFY** - Part of public contract

**Critical Constraints**:
```python
# IMMUTABLE: Model pinning for deterministic responses
ChatOpenAI(model="gpt-4.1-mini")
OpenAIEmbeddings(model="text-embedding-3-small")
```

#### **Tier 2: Development Workflow** (REQUIRED)
**Contents**: Environment setup, testing, quality assurance
**Location**: `.venv/`, testing infrastructure, CI/CD
**Rule**: ✅ **REQUIRED** - Must maintain for system operation

#### **Tier 3: RAG Foundation** (IMMUTABLE)
**Contents**: LangChain patterns, retrieval strategies, core business logic
**Location**: `src/rag/` directory structure
**Rule**: ❌ **NEVER MODIFY** - Core RAG algorithms and patterns

**Protected Components**:
```python
# IMMUTABLE: Core RAG business logic
src/rag/chain.py        # LangChain LCEL patterns
src/rag/vectorstore.py  # Qdrant integration
src/rag/retriever.py    # Retrieval factory patterns
src/rag/embeddings.py   # OpenAI embedding wrapper
```

#### **Tier 4: MCP Interface** (INTERFACE ONLY)
**Contents**: FastAPI→MCP conversion, interface layer
**Location**: `src/api/app.py`, `src/mcp/server.py`, `src/mcp/resources.py`
**Rule**: ✅ **SAFE TO MODIFY** - Interface layer only, never core logic

#### **Tier 5: Schema Management** (TOOLING)
**Contents**: Export, validation, compliance tooling
**Location**: `scripts/` directory
**Rule**: ✅ **SAFE TO MODIFY** - Tooling and development aids

## Decision

### **Immutable Tier Enforcement**

We will **strictly enforce** the tier-based architecture constraints to maintain system integrity and ensure the adv-rag repository continues to serve as a stable, production-ready RAG service provider.

#### **TIER 1: Project Core - IMMUTABLE**

**Never Modify**:
- Model pinning configurations (`gpt-4.1-mini`, `text-embedding-3-small`)
- Core settings and environment variable handling
- Import conventions and package structure

**Rationale**:
- Model pinning ensures deterministic responses across ecosystem
- Stable embedding dimensions required for vector database consistency
- Public contract for all consumers (DeepAgents, rag-eval-foundations)

**Validation**:
```python
# Enforcement check
def validate_model_pinning():
    assert settings.openai_model_name == "gpt-4.1-mini"
    assert settings.embedding_model_name == "text-embedding-3-small"
```

#### **TIER 2: Development Workflow - REQUIRED**

**Must Maintain**:
- Virtual environment activation procedures
- Testing infrastructure and patterns
- Code quality tools (ruff, black)

**Rationale**:
- System fails without proper environment setup
- Quality assurance prevents regression
- Development consistency across team

#### **TIER 3: RAG Foundation - IMMUTABLE**

**Never Modify**:
- Core RAG business logic in `src/rag/` directory
- LangChain LCEL chain construction patterns
- Retrieval factory patterns and implementations
- Vector database integration patterns

**Rationale**:
- Proven, production-tested implementations
- Breaking changes affect all consumers
- Complex optimization already completed

**Protection Pattern**:
```python
# Code review enforcement
def protected_directories():
    return [
        "src/rag/",           # Core RAG implementations
        "src/core/settings.py", # Model pinning
        "src/integrations/llm_models.py"  # LLM wrappers
    ]
```

#### **TIER 4: MCP Interface - SAFE MODIFICATION ZONE**

**Safe to Modify**:
- FastAPI endpoint definitions (`src/api/app.py`)
- MCP server configuration (`src/mcp/server.py`)
- MCP resources implementation (`src/mcp/resources.py`)
- Docker configuration and infrastructure setup

**Pattern for Safe Extensions**:
```python
# ✅ SAFE: Add new FastAPI endpoints (auto-converts to MCP tools)
@app.post("/invoke/new_retriever")
async def new_retriever(request: RetrievalRequest):
    # Use existing RAG foundation components
    return await existing_rag_chain.ainvoke(request.question)

# ❌ FORBIDDEN: Modify core RAG logic
# def modify_existing_retriever():  # NEVER DO THIS
```

#### **TIER 5: Schema Management - TOOLING ZONE**

**Safe to Modify**:
- Evaluation scripts (`scripts/evaluation/`)
- Ingestion pipelines (`scripts/ingestion/`)
- Migration utilities (`scripts/migration/`)
- All testing and validation tools

## Implementation Patterns

### **1. Interface Extension Pattern**

When adding new functionality, **always extend through Tier 4** (interface layer):

```python
# Correct pattern: Extend via FastAPI interface
@app.post("/invoke/specialized_retriever")
async def specialized_retriever(request: SpecialRequest):
    # ✅ Use existing Tier 3 components
    base_chain = create_rag_chain(retriever, llm)
    # ✅ Add interface-layer processing
    processed_request = preprocess_special_request(request)
    return await base_chain.ainvoke(processed_request)
```

### **2. Configuration Extension Pattern**

New configurations must respect Tier 1 immutability:

```python
# ✅ SAFE: Add new optional configurations
class Settings(BaseSettings):
    # IMMUTABLE CORE
    openai_model_name: str = "gpt-4.1-mini"  # NEVER CHANGE
    embedding_model_name: str = "text-embedding-3-small"  # NEVER CHANGE

    # ✅ SAFE: New optional settings
    new_feature_enabled: bool = False
    custom_timeout: int = 30
```

### **3. Testing Pattern for Tier Compliance**

```python
def test_tier_immutability():
    """Ensure core tiers remain unchanged"""
    # Tier 1: Model pinning
    assert get_llm().model_name == "gpt-4.1-mini"
    assert get_embeddings().model == "text-embedding-3-small"

    # Tier 3: Core patterns exist
    assert callable(create_rag_chain)
    assert issubclass(BaseRetriever, ABC)
```

### **4. Development Decision Matrix**

| Change Type | Tier | Allowed | Pattern |
|-------------|------|---------|---------|
| Add new endpoint | 4 | ✅ | FastAPI endpoint → MCP auto-conversion |
| Modify retrieval algorithm | 3 | ❌ | Use existing algorithms via interface |
| Add configuration | 1 | ⚠️ | Only if doesn't affect core models |
| Add MCP resource | 4 | ✅ | Native FastMCP resource registration |
| Modify chain logic | 3 | ❌ | Compose existing chains via interface |
| Add evaluation script | 5 | ✅ | Scripts directory additions |
| Change model names | 1 | ❌ | Public contract violation |
| Add Docker service | 4 | ✅ | Infrastructure configuration |

## Monitoring and Compliance

### **Automated Tier Validation**

```bash
# Pre-commit hook validation
./scripts/validate-tier-compliance.sh

# Expected checks:
✅ Tier 1: Model pinning unchanged
✅ Tier 3: Core RAG files unmodified
✅ Tier 4: Interface changes only
✅ All tests passing
```

### **Architecture Review Checklist**

```markdown
## Tier Compliance Review
- [ ] No modifications to `src/rag/` directory
- [ ] Model pinning configurations unchanged
- [ ] New functionality added via Tier 4 interfaces only
- [ ] Existing tests continue to pass
- [ ] New tests added for interface changes
```

### **Performance Impact Validation**

```python
# Ensure tier compliance doesn't affect performance
def validate_performance_maintained():
    # Existing performance benchmarks must pass
    assert retrieval_time < timedelta(seconds=2)
    assert full_workflow_time < timedelta(seconds=8)
```

## Integration Constraints

### **For DeepAgents Integration**
- ✅ **Can use**: All MCP tools and resources via Tier 4 interfaces
- ❌ **Cannot modify**: Core RAG implementations
- ✅ **Can extend**: New MCP tools for specific agent workflows

### **For rag-eval-foundations Integration**
- ✅ **Can evaluate**: All existing retrieval strategies
- ❌ **Cannot change**: RAG algorithm implementations
- ✅ **Can add**: New evaluation metrics via Tier 5 scripts

### **For External Integrations**
- ✅ **Stable API**: Tier 4 MCP interfaces provide stable integration points
- ❌ **Internal APIs**: Never depend on Tier 1-3 internal implementations
- ✅ **Extension Points**: Use FastAPI auto-conversion for new tools

## Consequences

### ✅ **Positive Outcomes**
- **Stability**: Core RAG functionality protected from breaking changes
- **Predictability**: Clear rules for what can be modified
- **Performance**: Optimized implementations preserved
- **Integration Safety**: Stable interfaces for external consumers

### ⚠️ **Development Constraints**
- **Limited Core Changes**: Cannot optimize core algorithms without architecture review
- **Interface-Only Extensions**: New features must work within existing patterns
- **Testing Requirements**: All changes must validate tier compliance

### 📋 **Action Items**
1. **Document Safe Patterns**: Create cookbook of approved extension patterns
2. **Implement Validation**: Automated tier compliance checking
3. **Training Materials**: Team education on tier-based development
4. **Review Process**: Architecture review for any Tier 1-3 modifications

## Examples

### **✅ Correct Extension Pattern**
```python
# Add new MCP tool via Tier 4 interface
@app.post("/invoke/domain_specific_retriever")
async def domain_specific_retriever(request: DomainRequest):
    # Use existing Tier 3 components
    retriever = create_retriever("semantic", vectorstore)
    llm = get_llm()  # Uses pinned model
    chain = create_rag_chain(retriever, llm)

    # Interface-layer customization
    domain_query = f"In {request.domain}: {request.question}"
    return await chain.ainvoke(domain_query)
```

### **❌ Incorrect Modification Pattern**
```python
# NEVER DO THIS - Modifying Tier 3 core logic
def modify_semantic_retriever():
    # ❌ This violates tier-based architecture
    # Changes to src/rag/retriever.py are forbidden
    pass
```

### **✅ Correct Configuration Extension**
```python
# Add new feature via safe configuration
class Settings(BaseSettings):
    # IMMUTABLE (Tier 1)
    openai_model_name: str = "gpt-4.1-mini"

    # ✅ SAFE (new optional feature)
    enable_query_caching: bool = True
    cache_ttl_seconds: int = 300
```

## References
- [Repository Separation Pattern](./adr-004-repository-separation-pattern.md)
- [MCP Integration Triangle Pattern](./adr-005-mcp-integration-triangle-pattern.md)
- [Feature Branch Strategy](./feature-branch-strategy.md)
- [adv-rag Architecture Documentation](../repos/adv-rag/CLAUDE.md)

---

**Key Principle**: The tier-based architecture ensures system stability by protecting core functionality (Tiers 1-3) while providing safe extension points (Tiers 4-5). All development must respect these immutable boundaries.