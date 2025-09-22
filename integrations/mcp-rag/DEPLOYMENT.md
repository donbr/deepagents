# DeepAgents MCP RAG - Production Deployment Guide

This guide covers production deployment scenarios for the DeepAgents MCP RAG system, from single-node Docker deployments to scalable Kubernetes clusters.

## 🏗️ Architecture Overview

### Production Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Production Environment                      │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Load Balancer │   MCP Servers   │   Infrastructure│ Monitoring│
│   (nginx/ALB)   │   (3+ replicas) │   (databases)   │ (Phoenix) │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

### Deployment Targets

- **Single Node**: Docker Compose for small-scale production
- **Kubernetes**: Scalable cluster deployment with auto-scaling
- **Cloud Native**: AWS/GCP/Azure with managed services
- **Hybrid**: On-premises with cloud observability

## 🐳 Docker Compose Deployment

### Production Configuration

Create `compose.prod.yaml`:

```yaml
version: '3.8'

services:
  # Production MCP server with multiple replicas
  mcp-server:
    image: ghcr.io/deepagents/mcp-rag:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
    environment:
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/deepagents
      - PHOENIX_COLLECTOR_ENDPOINT=http://phoenix:4317
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    command: >
      python -m deepagents_mcp_rag.mcp.server
      --transport http
      --host 0.0.0.0
      --port 6277
      --workers 4
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6277/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - deepagents-network

  # Production load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - mcp-server
    networks:
      - deepagents-network

  # High-availability Qdrant
  qdrant:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
    volumes:
      - qdrant_data:/qdrant/storage
      - ./qdrant.yaml:/qdrant/config/production.yaml:ro
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
    networks:
      - deepagents-network

  # Redis with persistence
  redis:
    image: redis:alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 60
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'
    networks:
      - deepagents-network

  # PostgreSQL with tuning
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: deepagents
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /data/postgres
    volumes:
      - postgres_data:/data/postgres
      - ./postgres.conf:/etc/postgresql/postgresql.conf:ro
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'
    networks:
      - deepagents-network

volumes:
  qdrant_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/qdrant
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/redis
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres

networks:
  deepagents-network:
    driver: bridge
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream mcp_servers {
        least_conn;
        server mcp-server_1:6277 max_fails=3 fail_timeout=30s;
        server mcp-server_2:6277 max_fails=3 fail_timeout=30s;
        server mcp-server_3:6277 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Health check endpoint
        location /health {
            proxy_pass http://mcp_servers/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # MCP API endpoints
        location /api/ {
            proxy_pass http://mcp_servers/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Observability dashboard
        location /phoenix/ {
            proxy_pass http://phoenix:6006/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Deployment Commands

```bash
# Production deployment
docker compose -f compose.yaml -f compose.prod.yaml up -d

# Scale MCP servers
docker compose -f compose.yaml -f compose.prod.yaml up -d --scale mcp-server=5

# Rolling updates
docker compose -f compose.yaml -f compose.prod.yaml pull mcp-server
docker compose -f compose.yaml -f compose.prod.yaml up -d mcp-server

# Health checks
curl http://localhost/health
curl http://localhost/api/tools/list
```

## ☸️ Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: deepagents
  labels:
    name: deepagents

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-rag-config
  namespace: deepagents
data:
  QDRANT_URL: "http://qdrant-service:6333"
  REDIS_URL: "redis://redis-service:6379"
  POSTGRES_URL: "postgresql://postgres:${POSTGRES_PASSWORD}@postgres-service:5432/deepagents"
  PHOENIX_COLLECTOR_ENDPOINT: "http://phoenix-service:4317"
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
```

### Secrets Management

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-rag-secrets
  namespace: deepagents
type: Opaque
stringData:
  ANTHROPIC_API_KEY: "your-api-key-here"
  POSTGRES_PASSWORD: "your-postgres-password"
  QDRANT_API_KEY: "your-qdrant-api-key"
```

### MCP Server Deployment

```yaml
# mcp-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: deepagents
  labels:
    app: mcp-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: ghcr.io/deepagents/mcp-rag:latest
        ports:
        - containerPort: 6277
          name: http
        envFrom:
        - configMapRef:
            name: mcp-rag-config
        - secretRef:
            name: mcp-rag-secrets
        command:
        - python
        - -m
        - deepagents_mcp_rag.mcp.server
        - --transport
        - http
        - --host
        - 0.0.0.0
        - --port
        - "6277"
        - --workers
        - "4"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 6277
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 6277
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

---
# mcp-server-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
  namespace: deepagents
  labels:
    app: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
  - name: http
    port: 6277
    targetPort: 6277
    protocol: TCP
  type: ClusterIP

---
# mcp-server-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
  namespace: deepagents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Infrastructure Services

```yaml
# qdrant-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: deepagents
spec:
  serviceName: qdrant-service
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
          name: http
        - containerPort: 6334
          name: grpc
        env:
        - name: QDRANT__SERVICE__HTTP_PORT
          value: "6333"
        - name: QDRANT__SERVICE__GRPC_PORT
          value: "6334"
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi

---
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: deepagents
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - "allkeys-lru"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-rag-ingress
  namespace: deepagents
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: mcp-rag-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mcp-server-service
            port:
              number: 6277
      - path: /phoenix
        pathType: Prefix
        backend:
          service:
            name: phoenix-service
            port:
              number: 6006
```

### Deployment Commands

```bash
# Deploy to Kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f mcp-server-deployment.yaml
kubectl apply -f qdrant-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f ingress.yaml

# Monitor deployment
kubectl get pods -n deepagents
kubectl logs -f deployment/mcp-server -n deepagents

# Scale deployment
kubectl scale deployment mcp-server --replicas=5 -n deepagents

# Rolling update
kubectl set image deployment/mcp-server mcp-server=ghcr.io/deepagents/mcp-rag:v1.2.0 -n deepagents
```

## ☁️ Cloud-Native Deployment

### AWS Deployment with EKS

```yaml
# aws-infrastructure.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-config
  namespace: deepagents
data:
  AWS_REGION: "us-west-2"
  QDRANT_URL: "https://your-qdrant-cluster.aws.qdrant.cloud"
  REDIS_URL: "redis://your-elasticache-cluster.cache.amazonaws.com:6379"
  POSTGRES_URL: "postgresql://username:password@your-rds-cluster.rds.amazonaws.com:5432/deepagents"

---
# Service with AWS Load Balancer
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
  namespace: deepagents
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: mcp-server
  ports:
  - port: 80
    targetPort: 6277
    protocol: TCP
```

### GCP Deployment with GKE

```yaml
# gcp-infrastructure.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gcp-config
  namespace: deepagents
data:
  GOOGLE_CLOUD_PROJECT: "your-project-id"
  QDRANT_URL: "https://your-qdrant-instance.gcp.qdrant.cloud"
  REDIS_URL: "redis://your-memorystore-instance:6379"
  POSTGRES_URL: "postgresql://username:password@your-cloud-sql-instance/deepagents"

---
# GCP Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-rag-ingress
  namespace: deepagents
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "mcp-rag-ip"
    networking.gke.io/managed-certificates: "mcp-rag-ssl-cert"
spec:
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: mcp-server-service
            port:
              number: 6277
```

## 📊 Monitoring and Observability

### Prometheus Monitoring

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: deepagents
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'mcp-server'
      static_configs:
      - targets: ['mcp-server-service:6277']
      metrics_path: /metrics
      scrape_interval: 10s
    - job_name: 'qdrant'
      static_configs:
      - targets: ['qdrant-service:6333']
      metrics_path: /metrics
    - job_name: 'redis'
      static_configs:
      - targets: ['redis-service:6379']
```

### Grafana Dashboards

```yaml
# grafana-dashboard-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-rag-dashboard
  namespace: deepagents
data:
  mcp-rag-dashboard.json: |
    {
      "dashboard": {
        "title": "DeepAgents MCP RAG Performance",
        "panels": [
          {
            "title": "Request Latency",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, mcp_request_duration_seconds_bucket)"
              }
            ]
          },
          {
            "title": "Retrieval Strategy Performance",
            "targets": [
              {
                "expr": "avg(mcp_retrieval_latency_seconds) by (strategy)"
              }
            ]
          },
          {
            "title": "Cache Hit Rate",
            "targets": [
              {
                "expr": "rate(mcp_cache_hits_total[5m]) / rate(mcp_cache_requests_total[5m])"
              }
            ]
          }
        ]
      }
    }
```

## 🔒 Security Configuration

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-rag-network-policy
  namespace: deepagents
spec:
  podSelector:
    matchLabels:
      app: mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 6277
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: qdrant
    ports:
    - protocol: TCP
      port: 6333
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Standards

```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: mcp-rag-psp
  namespace: deepagents
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 📋 Maintenance and Operations

### Backup Procedures

```bash
# PostgreSQL backup
kubectl exec -n deepagents postgres-0 -- pg_dump -U postgres deepagents > backup-$(date +%Y%m%d).sql

# Qdrant backup
kubectl exec -n deepagents qdrant-0 -- tar czf - /qdrant/storage | kubectl cp deepagents/qdrant-0:- qdrant-backup-$(date +%Y%m%d).tar.gz

# Redis backup
kubectl exec -n deepagents redis-0 -- redis-cli BGSAVE
kubectl cp deepagents/redis-0:/data/dump.rdb redis-backup-$(date +%Y%m%d).rdb
```

### Disaster Recovery

```bash
# PostgreSQL restore
kubectl cp backup-20240101.sql deepagents/postgres-0:/tmp/
kubectl exec -n deepagents postgres-0 -- psql -U postgres -d deepagents -f /tmp/backup-20240101.sql

# Qdrant restore
kubectl cp qdrant-backup-20240101.tar.gz deepagents/qdrant-0:/tmp/
kubectl exec -n deepagents qdrant-0 -- tar xzf /tmp/qdrant-backup-20240101.tar.gz -C /

# Redis restore
kubectl cp redis-backup-20240101.rdb deepagents/redis-0:/data/dump.rdb
kubectl delete pod -n deepagents redis-0  # Restart to load backup
```

### Performance Tuning

```yaml
# Resource optimization
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1"

# JVM tuning for large workloads
env:
- name: JAVA_OPTS
  value: "-Xmx1g -Xms512m -XX:+UseG1GC"

# Database connection pooling
- name: DB_POOL_SIZE
  value: "20"
- name: DB_MAX_OVERFLOW
  value: "10"
```

This deployment guide provides comprehensive coverage for production deployments across different environments and scales. Choose the approach that best fits your infrastructure requirements and operational capabilities.