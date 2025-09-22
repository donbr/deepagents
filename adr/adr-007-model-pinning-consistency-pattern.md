# ADR-007: Model Pinning Consistency Pattern

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

The DeepAgents ecosystem requires **deterministic responses** and **stable embedding dimensions** across all three repositories to ensure reliable evaluation, consistent behavior, and maintainable vector databases. Analysis reveals that model consistency is enforced as an **immutable constraint** in the production systems.

### Current Model Usage Analysis

#### **adv-rag Repository** (Production RAG Service)
**Model Pinning Status**: ✅ **ENFORCED** - Tier 1 immutable constraint
```python
# src/core/settings.py - IMMUTABLE
ChatOpenAI(model="gpt-4.1-mini")
OpenAIEmbeddings(model="text-embedding-3-small")
```

**Rationale from Documentation**:
- "Part of the public contract for deterministic responses"
- "Stable embedding dimensions required for vector database consistency"
- Tier 1 constraint: ❌ **NEVER MODIFY**

#### **rag-eval-foundations Repository** (Evaluation Pipeline)
**Model Pinning Status**: ✅ **DOCUMENTED** - Required for evaluation consistency
```python
# .env.example - Model requirements
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Rationale**:
- RAGAS evaluation requires consistent model behavior for reliable metrics
- Golden dataset validation depends on deterministic responses
- Cross-strategy comparison needs stable baseline

#### **DeepAgents Repository** (Agent Framework)
**Model Pinning Status**: 🟡 **FRAMEWORK-LEVEL** - Uses model provided by tools
**Pattern**: Inherits models from integrated MCP services (adv-rag)

**Implicit Consistency**: DeepAgents uses adv-rag via MCP, inheriting model consistency

### Business Requirements for Model Consistency

#### **1. Deterministic Evaluation**
- RAGAS metrics must be comparable across time
- Golden dataset results must be reproducible
- A/B testing requires consistent baseline behavior

#### **2. Vector Database Stability**
- Embedding dimensions must remain constant (1536 for text-embedding-3-small)
- Vector collections cannot be rebuilt for model changes
- Index structures depend on consistent vector dimensions

#### **3. Cross-Repository Integration**
- Agent workflows must produce predictable results
- Evaluation pipelines must measure actual system behavior
- Performance benchmarks must be meaningful over time

#### **4. Production Reliability**
- Model changes can introduce breaking behavioral changes
- Unexpected model updates could affect system performance
- Cost optimization requires predictable token usage patterns

## Decision

### **Ecosystem-Wide Model Pinning Standard**

We will **enforce consistent model usage** across all repositories in the DeepAgents ecosystem to ensure deterministic behavior, stable evaluation, and reliable production operation.

#### **Required Models for All Repositories**

##### **LLM Operations: `gpt-4.1-mini`**
```python
# Required across all repositories
ChatOpenAI(model="gpt-4.1-mini")
```

**Rationale**:
- **Performance**: Optimized for reasoning tasks while maintaining cost efficiency
- **Consistency**: Deterministic responses for evaluation and testing
- **Stability**: Long-term support model with predictable behavior
- **Capability**: Sufficient reasoning for RAG synthesis and agent planning

##### **Embedding Operations: `text-embedding-3-small`**
```python
# Required across all repositories
OpenAIEmbeddings(model="text-embedding-3-small")
```

**Rationale**:
- **Dimension Stability**: 1536 dimensions compatible with existing vector databases
- **Performance**: Optimized for semantic similarity with reasonable cost
- **Consistency**: Stable embeddings for reproducible retrieval
- **Integration**: Compatible with Qdrant and PostgreSQL/pgvector

#### **Enforcement Levels by Repository**

##### **adv-rag: IMMUTABLE (Tier 1 Constraint)**
```python
# NEVER CHANGE - Part of public contract
class Settings(BaseSettings):
    openai_model_name: str = "gpt-4.1-mini"  # IMMUTABLE
    embedding_model_name: str = "text-embedding-3-small"  # IMMUTABLE
```

**Enforcement**: Code review rejection for any changes to these values

##### **rag-eval-foundations: EVALUATION REQUIREMENT**
```python
# Required for consistent evaluation
DEFAULT_LLM_MODEL = "gpt-4.1-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Validation in pipeline
def validate_model_consistency():
    assert llm.model_name == "gpt-4.1-mini"
    assert embeddings.model == "text-embedding-3-small"
```

**Enforcement**: Evaluation pipeline fails if incorrect models detected

##### **DeepAgents: INTEGRATION INHERITANCE**
```python
# Inherits via MCP integration with adv-rag
# No direct model configuration needed
# Consistency enforced through service integration
```

**Enforcement**: Integration tests validate model consistency via MCP

## Implementation Patterns

### **1. Configuration Validation Pattern**

```python
# Shared validation across repositories
def validate_ecosystem_models(llm, embeddings):
    """Ensure ecosystem-wide model consistency"""
    required_llm = "gpt-4.1-mini"
    required_embedding = "text-embedding-3-small"

    if llm.model_name != required_llm:
        raise ValueError(f"LLM must be {required_llm}, got {llm.model_name}")

    if embeddings.model != required_embedding:
        raise ValueError(f"Embedding must be {required_embedding}, got {embeddings.model}")

    return True
```

### **2. Environment Variable Standardization**

```bash
# Standard environment variables across all repositories
export OPENAI_MODEL_NAME="gpt-4.1-mini"
export EMBEDDING_MODEL_NAME="text-embedding-3-small"

# Optional: Override only if absolutely necessary
# export ALLOW_MODEL_OVERRIDE="false"  # Production safety
```

### **3. Testing Pattern for Model Consistency**

```python
# Cross-repository test pattern
def test_model_pinning_compliance():
    """Validate model consistency across ecosystem"""

    # Test 1: Configuration matches standard
    settings = get_settings()
    assert settings.openai_model_name == "gpt-4.1-mini"
    assert settings.embedding_model_name == "text-embedding-3-small"

    # Test 2: Actual model instances match
    llm = get_llm()
    embeddings = get_embeddings()
    validate_ecosystem_models(llm, embeddings)

    # Test 3: Vector dimensions are correct
    test_embedding = embeddings.embed_query("test")
    assert len(test_embedding) == 1536  # text-embedding-3-small dimension
```

### **4. Migration Pattern for Model Updates**

```python
# IF model updates are required (rare), use migration pattern
class ModelMigration:
    """Handle rare cases requiring model updates"""

    def __init__(self):
        self.old_model = "gpt-4.1-mini"
        self.new_model = "new-model-name"  # Hypothetical

    def validate_migration_requirements(self):
        """Ensure migration is safe and necessary"""
        # 1. Verify new model has same embedding dimensions
        # 2. Validate performance benchmarks
        # 3. Ensure evaluation compatibility
        # 4. Plan vector database migration if needed
        pass

    def execute_coordinated_migration(self):
        """Update all repositories simultaneously"""
        # This would require careful coordination
        pass
```

## Vector Database Implications

### **Embedding Dimension Consistency**

```python
# Critical constraint for vector databases
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small

# Qdrant collection configuration (adv-rag)
collection_config = {
    "vectors": {
        "size": EMBEDDING_DIMENSION,  # Must match embedding model
        "distance": "Cosine"
    }
}

# PostgreSQL pgvector configuration (rag-eval-foundations)
CREATE TABLE documents (
    embedding vector(1536)  -- Must match embedding model
);
```

### **Migration Complexity**

**If embedding model changes**:
1. **Vector Recomputation**: All documents must be re-embedded
2. **Index Rebuilding**: Vector database indexes must be reconstructed
3. **Evaluation Reset**: All baseline metrics must be recalculated
4. **Performance Impact**: Temporary degradation during migration

**Cost**: Estimated 10+ hours for full ecosystem migration

## Performance and Cost Implications

### **Token Usage Optimization**

```python
# Model selection balances capability vs cost
GPT_4_1_MINI_CHARACTERISTICS = {
    "input_cost_per_1k_tokens": "$0.00015",
    "output_cost_per_1k_tokens": "$0.0006",
    "reasoning_capability": "high",
    "speed": "fast",
    "context_window": "128k tokens"
}

TEXT_EMBEDDING_3_SMALL_CHARACTERISTICS = {
    "cost_per_1k_tokens": "$0.00002",
    "dimensions": 1536,
    "performance": "high quality",
    "speed": "fast"
}
```

### **Performance Targets with Pinned Models**

- **Raw Retrieval**: <2s (embedding model performance critical)
- **Full RAG Pipeline**: <8s (LLM generation time dominant)
- **Evaluation Consistency**: Stable metrics over time

## Monitoring and Compliance

### **Automated Model Validation**

```bash
# CI/CD validation across repositories
./scripts/validate-model-consistency.sh

# Expected output
✅ adv-rag: Models pinned correctly (gpt-4.1-mini, text-embedding-3-small)
✅ rag-eval-foundations: Evaluation models consistent
✅ DeepAgents: Integration inherits correct models
✅ Vector dimensions: 1536 (text-embedding-3-small compatible)
```

### **Runtime Monitoring**

```python
# Production monitoring
def monitor_model_consistency():
    """Monitor actual model usage in production"""
    metrics = {
        "llm_model_calls": count_by_model(),
        "embedding_model_calls": count_by_embedding_model(),
        "unexpected_model_usage": detect_model_drift(),
        "vector_dimension_consistency": validate_vector_dimensions()
    }
    return metrics
```

### **Cost Tracking**

```python
# Track costs to validate model choice
def track_model_costs():
    """Monitor costs to ensure model pinning remains optimal"""
    return {
        "total_llm_tokens": get_llm_token_usage(),
        "total_embedding_tokens": get_embedding_token_usage(),
        "cost_per_operation": calculate_unit_costs(),
        "cost_trend": analyze_cost_trends()
    }
```

## Consequences

### ✅ **Positive Outcomes**
- **Deterministic Evaluation**: RAGAS metrics are reliable and comparable
- **System Stability**: Predictable behavior across all repositories
- **Vector Database Integrity**: No unexpected dimension changes
- **Cost Predictability**: Known and optimized token costs

### ⚠️ **Constraints and Risks**
- **Model Evolution**: Cannot easily adopt newer/better models
  - *Mitigation*: Formal migration process for necessary updates
- **Performance Optimization**: Limited to current model capabilities
  - *Mitigation*: Optimize prompts and retrieval strategies within constraints
- **Cost Increases**: If OpenAI raises prices for pinned models
  - *Mitigation*: Monitor costs and plan migration if necessary

### 📋 **Implementation Requirements**
1. **Validation Scripts**: Automated model consistency checking
2. **Documentation Updates**: Clear model requirements in all READMEs
3. **Testing Framework**: Cross-repository model validation
4. **Migration Planning**: Process for rare model updates

## Examples

### **✅ Correct Model Usage**
```python
# adv-rag repository
def create_llm():
    return ChatOpenAI(
        model="gpt-4.1-mini",  # ✅ Ecosystem standard
        temperature=0.0
    )

def create_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small"  # ✅ Ecosystem standard
    )
```

### **❌ Incorrect Model Usage**
```python
# Never do this - breaks ecosystem consistency
def create_wrong_llm():
    return ChatOpenAI(
        model="gpt-4"  # ❌ Wrong model
    )

def create_wrong_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-ada-002"  # ❌ Wrong dimensions
    )
```

### **✅ Environment-Based Configuration**
```python
# Flexible but consistent configuration
class Settings(BaseSettings):
    # Core pinning (never override in production)
    openai_model_name: str = "gpt-4.1-mini"
    embedding_model_name: str = "text-embedding-3-small"

    # Optional parameters (can be tuned)
    temperature: float = 0.0
    max_tokens: Optional[int] = None
```

## References
- [Tier-Based Architecture Constraints](./adr-006-tier-based-architecture-constraints.md)
- [Repository Separation Pattern](./adr-004-repository-separation-pattern.md)
- [MCP Integration Triangle Pattern](./adr-005-mcp-integration-triangle-pattern.md)
- [OpenAI Model Documentation](https://platform.openai.com/docs/models)

---

**Key Principle**: Model pinning ensures ecosystem consistency, deterministic evaluation, and system stability. The pinned models (`gpt-4.1-mini`, `text-embedding-3-small`) are immutable constraints that all repositories must respect.