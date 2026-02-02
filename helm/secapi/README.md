# SecAPI Helm Chart

Kubernetes Helm chart for deploying SecAPI.

## Quick Start

### 1. Build the image

```bash
docker build -t secapi:latest .

# Load into your cluster (Kind/Colima/Minikube)
kind load docker-image secapi:latest --name colima
# OR for Colima:
docker save secapi:latest | colima load -
```

### 2. Install

```bash
helm install secapi ./helm/secapi \
  --set postgres.postgresPassword=changeme \
  --namespace secapi --create-namespace
```

### 3. Access

```bash
# API
kubectl port-forward svc/secapi-api 8000:8000 -n secapi
# Open http://localhost:8000

# Flower (Celery monitor)
kubectl port-forward svc/secapi-flower 5555:5555 -n secapi
# Open http://localhost:5555
```

## Using External Database (Optional)

For production with managed databases (AWS RDS, Cloud SQL, etc.):

```bash
kubectl create secret generic secapi-secrets \
  --from-literal=secret-key='$(openssl rand -base64 32)' \
  --from-literal=database-url='postgresql+asyncpg://user:pass@external-db:5432/secapi' \
  --from-literal=redis-url='redis://external-redis:6379/0' \
  --from-literal=celery-broker-url='redis://external-redis:6379/1' \
  --from-literal=celery-result-backend='redis://external-redis:6379/2'

helm install secapi ./helm/secapi \
  --set postgres.enabled=false \
  --set redis.enabled=false \
  --set existingSecret=secapi-secrets \
  --namespace secapi --create-namespace
```

**For local development**, skip this - the chart includes PostgreSQL and Redis.

## Commands

```bash
# Check pods
kubectl get pods -n secapi

# Logs
kubectl logs -f deployment/secapi-api -n secapi

# Upgrade
helm upgrade secapi ./helm/secapi -n secapi

# Uninstall
helm uninstall secapi -n secapi
kubectl delete pvc -n secapi --all
```
