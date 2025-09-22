#!/bin/bash

# =============================================================================
# DeepAgents Shared Infrastructure Connection Helper
# =============================================================================
# Helps DeepAgents repository connect to the unified infrastructure
# hosted in rag-eval-foundations

set -e

echo "🔗 DeepAgents → Shared Infrastructure Connection"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Infrastructure repository path
INFRA_REPO="/home/donbr/sept2025/deepagents/repos/rag-eval-foundations"

echo "📍 Infrastructure repository: $INFRA_REPO"
echo ""

# Check if infrastructure repository exists
if [ ! -d "$INFRA_REPO" ]; then
    echo -e "❌ ${RED}Infrastructure repository not found at $INFRA_REPO${NC}"
    echo "   Please ensure rag-eval-foundations is checked out"
    exit 1
fi

echo "🔍 Checking shared infrastructure status..."

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    local description=$3

    if curl -s "$health_url" > /dev/null 2>&1; then
        echo -e "✅ ${GREEN}$service_name ($description) - Available${NC}"
        return 0
    else
        echo -e "❌ ${RED}$service_name ($description) - Not available${NC}"
        return 1
    fi
}

# Check Redis
check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "✅ ${GREEN}Redis (Cache) - Available${NC}"
        return 0
    else
        echo -e "❌ ${RED}Redis (Cache) - Not available${NC}"
        return 1
    fi
}

# Check all services
services_available=0
total_services=5

echo ""
echo "🏥 Service Health Checks:"

check_service "PostgreSQL" "postgresql://langchain:langchain@localhost:6024/langchain" "Database" || true
if [ $? -eq 0 ]; then services_available=$((services_available + 1)); fi

check_service "Qdrant" "http://localhost:6333/health" "Vector DB" || true
if [ $? -eq 0 ]; then services_available=$((services_available + 1)); fi

check_redis || true
if [ $? -eq 0 ]; then services_available=$((services_available + 1)); fi

check_service "Phoenix" "http://localhost:6006/health" "Observability" || true
if [ $? -eq 0 ]; then services_available=$((services_available + 1)); fi

check_service "RedisInsight" "http://localhost:5540" "Cache UI" || true
if [ $? -eq 0 ]; then services_available=$((services_available + 1)); fi

echo ""

if [ $services_available -eq $total_services ]; then
    echo -e "🎉 ${GREEN}All shared services are available!${NC}"
    echo ""
    echo "🔧 Environment variables for DeepAgents:"
    echo "   export POSTGRES_URL='postgresql://langchain:langchain@localhost:6024/langchain'"
    echo "   export QDRANT_URL='http://localhost:6333'"
    echo "   export REDIS_URL='redis://localhost:6379'"
    echo "   export PHOENIX_ENDPOINT='http://localhost:6006'"
    echo "   export PHOENIX_OTLP_ENDPOINT='http://localhost:4317'"
    echo ""
    echo "📝 Add these to your .env file or export them before running DeepAgents"

elif [ $services_available -gt 0 ]; then
    echo -e "⚠️  ${YELLOW}Partial infrastructure available ($services_available/$total_services)${NC}"
    echo ""
    echo "🚀 To start missing services:"
    echo "   cd $INFRA_REPO"
    echo "   docker-compose up -d"
    echo ""
else
    echo -e "❌ ${RED}No shared infrastructure services available${NC}"
    echo ""
    echo "🚀 To start infrastructure:"
    echo "   cd $INFRA_REPO"
    echo "   ./scripts/check-services.sh"
    echo "   docker-compose up -d"
    echo ""
fi

echo "🔍 Infrastructure management commands:"
echo "   Start:   cd $INFRA_REPO && docker-compose up -d"
echo "   Stop:    cd $INFRA_REPO && docker-compose down"
echo "   Status:  cd $INFRA_REPO && docker ps --filter 'label=project=deepagents-ecosystem'"
echo "   Logs:    cd $INFRA_REPO && docker-compose logs -f [service]"
echo ""