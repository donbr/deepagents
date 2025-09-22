# ADR-008: Infrastructure Centralization Pattern

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

The DeepAgents ecosystem initially suffered from **port conflicts**, **resource duplication**, and **management complexity** with each repository maintaining its own Docker infrastructure. Analysis revealed significant operational overhead and integration challenges that required a unified approach.

### Infrastructure Conflict Analysis

#### **Original State: Distributed Infrastructure**

**DeepAgents Repository**:
```yaml
# integrations/mcp-rag/compose.yaml
services:
  phoenix: 6006:6006, 4317:4317, 4318:4318
  qdrant: 6333:6333, 6334:6334
  redis: 6379:6379
  postgres: 5432:5432
```

**adv-rag Repository**:
```yaml
# docker-compose.yml
services:
  phoenix: 6006:6006, 4317:4317
  qdrant: 6333:6333, 6334:6334
  redis: 6379:6379
  redisinsight: 5540:5540
```

**rag-eval-foundations Repository**:
```yaml
# docker-compose.yml
services:
  phoenix: 6006:6006, 4317:4317
  postgres: 6024:5432  # Different port to avoid conflicts
```

#### **Problems Identified**

**1. Port Conflicts**: Multiple services attempting to bind to same ports
```bash
# Typical conflict scenario
❌ Port 6006 (Phoenix-UI) is in use
❌ Port 4317 (Phoenix-OTLP-gRPC) is in use
❌ Port 6379 (Redis) is in use
```

**2. Resource Duplication**: 3x infrastructure overhead
- 3 separate Phoenix instances for same ecosystem
- 3 separate Redis instances with redundant data
- Inconsistent service configurations across repositories

**3. Management Complexity**: No unified control
- Services started/stopped independently
- Inconsistent health checking
- No ecosystem-wide service discovery

#### **Business Impact**
- **Development Friction**: Developers unable to run full ecosystem
- **Integration Testing**: Cannot validate cross-repository workflows
- **Resource Waste**: Unnecessary compute and memory overhead
- **Observability Fragmentation**: Traces scattered across multiple Phoenix instances

### Strategic Analysis

#### **Infrastructure Host Candidates**

**DeepAgents**: ❌ **Unsuitable**
- Primary role is agent orchestration, not infrastructure
- Adding infrastructure responsibility violates separation of concerns
- No natural affinity for Docker service management

**adv-rag**: ⚠️ **Possible but Suboptimal**
- Production RAG service should focus on core competency
- Tier-based architecture constraints limit infrastructure flexibility
- No PostgreSQL requirements (uses Qdrant only)

**rag-eval-foundations**: ✅ **Optimal Choice**
- Already manages comprehensive Docker configuration
- Natural infrastructure management role (evaluation requires orchestration)
- PostgreSQL expertise and pgvector requirements
- Most complete health check and monitoring framework

## Decision

### **Centralized Infrastructure in rag-eval-foundations**

We will **consolidate all Docker infrastructure** into the rag-eval-foundations repository, which will serve as the **infrastructure host** for the entire DeepAgents ecosystem.

#### **rag-eval-foundations as Infrastructure Host**

**Location**: `/home/donbr/sept2025/deepagents/repos/rag-eval-foundations/docker-compose.yml`

**Responsibilities**:
1. **Service Orchestration**: All Docker services for ecosystem
2. **Port Management**: Standard port allocation and conflict prevention
3. **Health Monitoring**: Comprehensive health checks for all services
4. **Network Management**: Unified Docker network for ecosystem
5. **Volume Management**: Persistent data storage coordination
6. **Service Discovery**: Health check scripts and connection helpers

#### **Unified Service Configuration**

```yaml
# Consolidated infrastructure in rag-eval-foundations
networks:
  deepagents-ecosystem:
    name: deepagents-ecosystem
    driver: bridge

services:
  # PostgreSQL with pgvector for evaluation data
  deepagents-postgres:
    ports: ["6024:5432"]
    labels: ["project=deepagents-ecosystem", "component=database"]

  # Qdrant vector database for RAG functionality
  deepagents-qdrant:
    ports: ["6333:6333", "6334:6334"]
    labels: ["project=deepagents-ecosystem", "component=vectordb"]

  # Redis for caching across all projects
  deepagents-redis:
    ports: ["6379:6379"]
    labels: ["project=deepagents-ecosystem", "component=cache"]

  # RedisInsight for cache management
  deepagents-redisinsight:
    ports: ["5540:5540"]
    labels: ["project=deepagents-ecosystem", "component=cache-ui"]

  # Phoenix observability for unified tracing
  deepagents-phoenix:
    ports: ["6006:6006", "4317:4317"]
    labels: ["project=deepagents-ecosystem", "component=observability"]
```

#### **Standard Port Allocation**

| Service | Port | Purpose | Standard Compliance |
|---------|------|---------|-------------------|
| Phoenix UI | 6006 | Web interface | ✅ Industry standard (TensorBoard) |
| Phoenix OTLP | 4317 | OpenTelemetry gRPC | ✅ OTLP standard |
| Qdrant HTTP | 6333 | Vector database API | ✅ Qdrant default |
| Qdrant gRPC | 6334 | Vector database gRPC | ✅ Qdrant default |
| Redis | 6379 | Cache operations | ✅ Redis default |
| PostgreSQL | 6024 | Evaluation database | ✅ Non-conflicting |
| RedisInsight | 5540 | Cache management UI | ✅ RedisInsight default |

### **Cross-Repository Integration Pattern**

#### **Service Discovery Scripts**

**rag-eval-foundations**:
```bash
# ./scripts/check-services.sh
# Validates port availability and service readiness
./scripts/check-services.sh
# Output: ✅ All ports available, ready to start services
```

**adv-rag**:
```bash
# ./scripts/infrastructure/connect-to-shared-infrastructure.sh
# Validates connection to shared infrastructure
✅ Qdrant (Vector DB) - Available
✅ Redis (Cache) - Available
✅ Phoenix (Observability) - Available
✅ RedisInsight (Cache UI) - Available
```

**DeepAgents**:
```bash
# ./scripts/infrastructure/connect-to-shared-infrastructure.sh
# Full ecosystem validation
✅ PostgreSQL (Database) - Available
✅ Qdrant (Vector DB) - Available
✅ Redis (Cache) - Available
✅ Phoenix (Observability) - Available
✅ RedisInsight (Cache UI) - Available
```

#### **Environment Variable Standardization**

```bash
# Standard environment variables for all repositories
export POSTGRES_URL="postgresql://langchain:langchain@localhost:6024/langchain"
export QDRANT_URL="http://localhost:6333"
export REDIS_URL="redis://localhost:6379"
export PHOENIX_ENDPOINT="http://localhost:6006"
export PHOENIX_OTLP_ENDPOINT="http://localhost:4317"
```

## Implementation Benefits

### **1. Eliminated Port Conflicts**
**Before**:
```bash
❌ Found 3 port conflicts
   Port 6006 (Phoenix) is in use
   Port 4317 (Phoenix-OTLP) is in use
   Port 6379 (Redis) is in use
```

**After**:
```bash
✅ All ports are available!
✅ All required services are available!
```

### **2. Reduced Resource Usage**
- **Memory**: ~75% reduction (1 Phoenix vs 3 Phoenix instances)
- **CPU**: ~60% reduction (consolidated services)
- **Storage**: Unified volumes with ecosystem-wide labeling
- **Network**: Single Docker network reduces overhead

### **3. Unified Observability**
```python
# Single Phoenix instance captures ecosystem-wide traces
phoenix_traces = {
    "deepagents": "Agent orchestration spans",
    "adv-rag": "RAG pipeline spans",
    "rag-eval-foundations": "Evaluation pipeline spans"
}
# Project-specific filtering via tags
```

### **4. Simplified Operations**
```bash
# Single command starts entire ecosystem
cd /home/donbr/sept2025/deepagents/repos/rag-eval-foundations
docker-compose up -d

# Single command stops entire ecosystem
docker-compose down

# Unified health checking
docker ps --filter 'label=project=deepagents-ecosystem'
```

## Operational Procedures

### **Infrastructure Lifecycle Management**

#### **Startup Sequence**
```bash
# 1. Port conflict detection
cd /home/donbr/sept2025/deepagents/repos/rag-eval-foundations
./scripts/check-services.sh

# 2. Infrastructure startup
docker-compose up -d

# 3. Health validation
docker ps --filter 'label=project=deepagents-ecosystem'

# 4. Service connectivity validation
curl http://localhost:6006/health  # Phoenix
curl http://localhost:6333/health  # Qdrant
redis-cli ping                     # Redis
```

#### **Cross-Repository Validation**
```bash
# adv-rag service discovery
cd /home/donbr/sept2025/deepagents/repos/adv-rag
./scripts/infrastructure/connect-to-shared-infrastructure.sh
# Expected: 4/4 services available

# DeepAgents service discovery
cd /home/donbr/sept2025/deepagents
./scripts/infrastructure/connect-to-shared-infrastructure.sh
# Expected: 5/5 services available
```

#### **Shutdown Sequence**
```bash
# Graceful shutdown
cd /home/donbr/sept2025/deepagents/repos/rag-eval-foundations
docker-compose down

# With data removal (if needed)
docker-compose down -v
```

### **Health Monitoring Framework**

#### **Service Health Checks**
```yaml
# Built into docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U langchain"]  # PostgreSQL
  test: ["CMD", "curl", "-f", "http://localhost:6333/health"]  # Qdrant
  test: ["CMD", "redis-cli", "ping"]  # Redis
  test: ["CMD", "curl", "-f", "http://localhost:6006/health"]  # Phoenix
  interval: 10s
  timeout: 5s
  retries: 5
```

#### **Automated Monitoring**
```bash
# Continuous health monitoring
watch -n 30 'docker ps --filter "label=project=deepagents-ecosystem" --format "table {{.Names}}\t{{.Status}}"'

# Expected output every 30s
deepagents-postgres     Up (healthy)
deepagents-qdrant       Up (healthy)
deepagents-redis        Up (healthy)
deepagents-phoenix      Up (healthy)
deepagents-redisinsight Up
```

## Integration Constraints

### **1. Infrastructure Dependencies**
- **All repositories** must validate shared infrastructure before operation
- **Service discovery scripts** are required in each repository
- **Standard environment variables** must be used for consistency

### **2. Resource Sharing Protocols**
- **Database Isolation**: Each repository uses distinct databases/collections
- **Cache Namespace**: Redis keys must be prefixed by repository
- **Observability Tagging**: Phoenix traces must include project tags

### **3. Coordination Requirements**
- **Startup Order**: Infrastructure must start before application services
- **Shutdown Coordination**: Applications should gracefully disconnect before infrastructure shutdown
- **Version Compatibility**: Docker images must remain compatible across updates

## Monitoring and Compliance

### **Infrastructure Health Metrics**
```python
def monitor_infrastructure_health():
    return {
        "service_availability": check_all_services_healthy(),
        "port_usage": validate_standard_ports(),
        "resource_usage": get_docker_resource_metrics(),
        "cross_repo_connectivity": validate_service_discovery()
    }
```

### **Resource Usage Tracking**
```bash
# Monitor infrastructure resource usage
docker stats $(docker ps --filter 'label=project=deepagents-ecosystem' -q)

# Track volume usage
docker system df

# Monitor network performance
docker network inspect deepagents-ecosystem
```

### **Compliance Validation**
```bash
# Automated compliance checking
./scripts/validate-infrastructure-compliance.sh

# Expected validations
✅ All services use deepagents-ecosystem network
✅ All containers use deepagents- prefix
✅ All volumes use deepagents_ prefix
✅ All services have project=deepagents-ecosystem label
✅ Standard ports are correctly mapped
```

## Consequences

### ✅ **Positive Outcomes**
- **Zero Port Conflicts**: Clean startup across all repositories
- **Resource Efficiency**: 60-75% reduction in infrastructure overhead
- **Unified Observability**: Single Phoenix instance for ecosystem tracing
- **Simplified Operations**: One infrastructure to manage
- **Integration Enablement**: Foundation for cross-repository workflows

### ⚠️ **Operational Considerations**
- **Single Point of Failure**: Infrastructure outage affects entire ecosystem
  - *Mitigation*: Comprehensive health checks and restart policies
- **Coordination Overhead**: Changes require cross-repository testing
  - *Mitigation*: Automated validation and service discovery scripts
- **Resource Contention**: Shared services could become bottlenecks
  - *Mitigation*: Monitoring and capacity planning

### 📋 **Maintenance Requirements**
1. **Regular Health Monitoring**: Automated infrastructure health validation
2. **Capacity Planning**: Monitor resource usage and plan for growth
3. **Version Management**: Coordinate Docker image updates across ecosystem
4. **Backup Strategy**: Ensure data persistence for evaluation and vector data

## Examples

### **✅ Correct Infrastructure Usage**
```bash
# Start infrastructure from designated host
cd /home/donbr/sept2025/deepagents/repos/rag-eval-foundations
./scripts/check-services.sh && docker-compose up -d

# Validate from consuming repositories
cd /home/donbr/sept2025/deepagents/repos/adv-rag
./scripts/infrastructure/connect-to-shared-infrastructure.sh
```

### **❌ Incorrect Infrastructure Usage**
```bash
# Never start competing infrastructure
cd /home/donbr/sept2025/deepagents/repos/adv-rag
docker-compose up -d  # ❌ Would create port conflicts
```

### **✅ Cross-Repository Integration**
```python
# Each repository connects to shared infrastructure
import os
PHOENIX_ENDPOINT = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
```

## References
- [Unified Infrastructure Implementation Summary](./unified-infrastructure-implementation-summary.md)
- [Repository Separation Pattern](./adr-004-repository-separation-pattern.md)
- [MCP Integration Triangle Pattern](./adr-005-mcp-integration-triangle-pattern.md)
- [ADR-003: Unified Infrastructure Strategy](./adr-003-unified-infrastructure-strategy.md)

---

**Key Principle**: Infrastructure centralization eliminates conflicts, reduces overhead, and enables ecosystem-wide integration while maintaining clear repository boundaries. rag-eval-foundations serves as the infrastructure host for the entire DeepAgents ecosystem.