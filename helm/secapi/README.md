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
  --set postgres.postgresPassword=changeme
```

Resources are deployed to the `secapi` namespace by default.

### 3. Access

```bash
# API
kubectl port-forward svc/secapi-api 8000:8000 -n secapi
# Open http://localhost:8000

# Flower (Celery monitor)
kubectl port-forward svc/secapi-flower 5555:5555 -n secapi
# Open http://localhost:5555
```

## Modes

| Mode | `production` | API Key Reset | Use Case |
|------|---------------|---------------|----------|
| Development | `false` | Console logging | Local testing |
| Production | `true` | Email via SMTP | Production deployment |

```bash
# Development (default)
helm install secapi ./helm/secapi --set production=false

# Production (with SMTP required)
helm install secapi ./helm/secapi --set production=true
```

## Production Setup

For production with managed databases (AWS RDS, Cloud SQL, etc.) and SMTP:

```bash
kubectl create secret generic secapi-secrets \
  --from-literal=secret-key='$(openssl rand -base64 32)' \
  --from-literal=database-url='postgresql+asyncpg://user:pass@external-db:5432/secapi' \
  --from-literal=redis-url='redis://external-redis:6379/0' \
  --from-literal=celery-broker-url='redis://external-redis:6379/1' \
  --from-literal=celery-result-backend='redis://external-redis:6379/2' \
  --from-literal=smtp-host='smtp.gmail.com' \
  --from-literal=smtp-port='587' \
  --from-literal=smtp-user='your-email@gmail.com' \
  --from-literal=smtp-password='your-app-password' \
  --from-literal=smtp-from='noreply@secapi.com' \
  --from-literal=smtp-use-tls='true'

helm install secapi ./helm/secapi \
  --set postgres.enabled=false \
  --set redis.enabled=false \
  --set production=true \
  --set existingSecret=secapi-secrets
```

## Testing Email Locally

Use [Mailhog](https://github.com/mailhog/MailHog) to test email without sending real emails:

```bash
# Install Mailhog
brew install mailhog
mailhog

# Or with Docker
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Configure Helm to use Mailhog
helm upgrade secapi ./helm/secapi \
  --set smtp.host='host.docker.internal' \
  --set smtp.port='1025' \
  --set production=true
```

Check emails at http://localhost:8025

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
