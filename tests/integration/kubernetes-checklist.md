# Kubernetes/Helm Deployment Integration Test Checklist

**Default Namespace:** `secapi`

---

## Pre-Deployment Checks

### Cluster Prerequisites
- [ ] Kubernetes cluster is accessible
  ```bash
  kubectl cluster-info
  ```
  Expected: Cluster control plane endpoints listed

- [ ] kubectl is configured correctly
  ```bash
  kubectl config current-context
  ```
  Expected: Current context name

- [ ] Sufficient cluster resources (nodes ready)
  ```bash
  kubectl get nodes
  ```
  Expected: All nodes in Ready state

- [ ] Default storage class is available (for PVCs)
  ```bash
  kubectl get storageclass
  ```
  Expected: At least one storageclass marked as (default)

### Helm Installation
- [ ] Helm 3+ is installed
  ```bash
  helm version
  ```
  Expected: Helm version v3.x.x

### Namespace Preparation
- [ ] Create namespace if not using `namespace.create: true`
  ```bash
  kubectl create namespace secapi --dry-run=client -o yaml
  ```
  Optional: Apply with `kubectl apply -f -`

### Values Configuration
- [ ] Custom values file prepared (if needed)
  ```bash
  helm show values helm/secapi > custom-values.yaml
  ```
  Edit `custom-values.yaml` as needed

---

## Deployment

### Install/Upgrade Helm Release
- [ ] Dry-run the installation
  ```bash
  helm install secapi helm/secapi \
    --namespace secapi \
    --values helm/secapi/values.yaml \
    --dry-run --debug
  ```
  Expected: No errors, manifests generated

- [ ] Install the release
  ```bash
  helm install secapi helm/secapi \
    --namespace secapi \
    --values helm/secapi/values.yaml \
    --timeout 10m
  ```
  Expected: Release `secapi` created

- [ ] Verify Helm release status
  ```bash
  helm status secapi --namespace secapi
  ```
  Expected: STATUS: deployed

### Verify Pod Startup
- [ ] All pods are running
  ```bash
  kubectl get pods -n secapi
  ```
  Expected: Pods in Running state with READY 1/1 (or higher)

- [ ] Wait for all pods to be ready
  ```bash
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=secapi -n secapi --timeout=300s
  ```
  Expected: Pods marked as ready

- [ ] Check for CrashLoopBackOff or ImagePullBackOff
  ```bash
  kubectl get pods -n secapi -o json | jq -r '.items[] | select(.status.phase!="Running") | .metadata.name'
  ```
  Expected: Empty (no failing pods)

---

## Service Health Checks

### API Service
- [ ] API service is created
  ```bash
  kubectl get svc secapi -n secapi
  ```
  Expected: Service exists with ClusterIP or LoadBalancer

- [ ] API service has endpoints
  ```bash
  kubectl get endpoints secapi -n secapi
  ```
  Expected: At least one endpoint IP listed

- [ ] Port-forward to test API locally
  ```bash
  kubectl port-forward -n secapi svc/secapi 8000:8000 &
  export PF_PID=$!
  sleep 3
  ```
  (Remember to kill after testing: `kill $PF_PID`)

### PostgreSQL Health
- [ ] PostgreSQL service is running
  ```bash
  kubectl get pods -n secapi -l app=postgres
  ```
  Expected: Pod in Running state

- [ ] PostgreSQL is accepting connections
  ```bash
  kubectl exec -n secapi <postgres-pod-name> -- pg_isready -U secapi
  ```
  Expected: `secapi:5432 - accepting connections`

### Redis Health
- [ ] Redis service is running
  ```bash
  kubectl get pods -n secapi -l app=redis
  ```
  Expected: Pod in Running state

- [ ] Redis is responding
  ```bash
  kubectl exec -n secapi <redis-pod-name> -- redis-cli ping
  ```
  Expected: `PONG`

### Celery Worker Health
- [ ] Worker pods are running
  ```bash
  kubectl get pods -n secapi -l app.kubernetes.io/component=worker
  ```
  Expected: Pod(s) in Running state

- [ ] Worker logs show readiness
  ```bash
  kubectl logs -n secapi <worker-pod-name> --tail=20
  ```
  Expected: `celery@worker ready.`

### Flower Health
- [ ] Flower service/pod is running
  ```bash
  kubectl get pods -n secapi -l app.kubernetes.io/component=flower
  ```
  Expected: Pod in Running state

- [ ] Port-forward to test Flower
  ```bash
  kubectl port-forward -n secapi svc/secapi-flower 5555:5555 &
  export FLOWER_PF_PID=$!
  sleep 3
  ```
  (Remember to kill after testing: `kill $FLOWER_PF_PID`)

---

## API Endpoint Tests

**Note:** These tests assume you've set up port-forward or have a LoadBalancer/Ingress configured.

**If using port-forward:**
```bash
export BASE_URL="http://localhost:8000"
```

**If using Ingress/LoadBalancer:**
```bash
export BASE_URL="http://<your-ingress-host>"
```

### Health Endpoints
- [ ] Root endpoint returns HTML
  ```bash
  curl -s $BASE_URL/ | head -10
  ```
  Expected: HTML content

- [ ] Health endpoint
  ```bash
  curl -s $BASE_URL/health | jq .
  ```
  Expected: `{"status": "healthy", ...}`

- [ ] API v1 health endpoint
  ```bash
  curl -s $BASE_URL/api/v1/health | jq .
  ```
  Expected: `{"status": "healthy", ...}`

### Authentication: User Registration
- [ ] Register a new user (save the returned `api_key`!)
  ```bash
  curl -s -X POST $BASE_URL/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "k8s-test@example.com"}' | jq .
  ```
  Expected: Response with `id`, `email`, `api_key`, `tier`, `created_at`

- [ ] Duplicate registration returns 409
  ```bash
  curl -s -X POST $BASE_URL/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "k8s-test@example.com"}' | jq .
  ```
  Expected: `{"detail": "User with this email already exists"}`

**Save your API key:**
```bash
export API_KEY="<api_key_from_registration>"
```

### Scans: Submit Docker Image Scan
- [ ] Submit a scan without API key returns 401
  ```bash
  curl -s -X POST $BASE_URL/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -d '{"image": "nginx:alpine"}' | jq .
  ```
  Expected: 401 Unauthorized

- [ ] Submit a scan with valid API key
  ```bash
  curl -s -X POST $BASE_URL/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "nginx:alpine"}' | jq .
  ```
  Expected: Response with `scan_id`, `status="queued"`

**Save the scan_id:**
```bash
export SCAN_ID="<scan_id_from_response>"
```

### Scans: Check Scan Status
- [ ] Get scan status
  ```bash
  curl -s $BASE_URL/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Status `pending`, `running`, or `completed`

- [ ] Get scan status (table format)
  ```bash
  curl -s "$BASE_URL/api/v1/scans/$SCAN_ID?format=table" \
    -H "Authorization: Bearer $API_KEY"
  ```
  Expected: Plain text table

### Scans: List Scans
- [ ] List all scans
  ```bash
  curl -s "$BASE_URL/api/v1/scans?page=1&page_size=10" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Response with `total`, `scans` array

- [ ] Filter by status
  ```bash
  curl -s "$BASE_URL/api/v1/scans?status=completed" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```

### Scans: Delete Scan
- [ ] Delete a completed scan
  ```bash
  # Wait for completion, then delete
  curl -s -X DELETE $BASE_URL/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" -w "\nHTTP: %{http_code}\n"
  ```
  Expected: HTTP 204

---

## Celery Worker Verification

### Worker Status (via Flower)
- [ ] Flower shows connected workers
  ```bash
  curl -s http://localhost:5555/api/workers | jq .
  ```
  Expected: JSON with worker info (after port-forward)

- [ ] Worker is processing tasks
  ```bash
  # Submit a scan
  curl -s -X POST $BASE_URL/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "alpine:latest"}' > /dev/null

  # Check tasks after a moment
  sleep 5 && curl -s http://localhost:5555/api/tasks | jq '. | length'
  ```
  Expected: Tasks listed

### Task Execution
- [ ] Scan completes successfully
  ```bash
  SCAN_ID=$(curl -s -X POST $BASE_URL/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "redis:7-alpine"}' | jq -r '.scan_id')

  for i in {1..60}; do
    STATUS=$(curl -s $BASE_URL/api/v1/scans/$SCAN_ID \
      -H "Authorization: Bearer $API_KEY" | jq -r '.status')
    echo "Attempt $i: $STATUS"
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
      break
    fi
    sleep 5
  done
  ```
  Expected: Final status is `completed`

---

## Database Connectivity

### Pod-to-Database Connectivity
- [ ] API pod can reach PostgreSQL
  ```bash
  kubectl exec -n secapi <api-pod-name> -- \
    python -c "
import asyncio
from app.db.session import get_db
async def test():
    async for db in get_db():
        print('DB connection: OK')
        break
asyncio.run(test())
"
  ```
  Expected: `DB connection: OK`

### Data Persistence
- [ ] Data persists across pod restarts
  ```bash
  # Register a user
  curl -s -X POST $BASE_URL/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "persist-k8s@test.com"}' | jq -r '.id' > /tmp/user_id.txt

  # Restart the API pod
  kubectl delete pod -n secapi -l app.kubernetes.io/name=secapi
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=secapi -n secapi --timeout=120s

  # Verify user still exists
  curl -s -X POST $BASE_URL/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "persist-k8s@test.com"}' | jq .
  ```
  Expected: 409 Conflict - user already exists

---

## Configuration Tests

### ConfigMap Verification
- [ ] ConfigMap is applied
  ```bash
  kubectl get configmap secapi-config -n secapi -o yaml
  ```
  Expected: ConfigMap with environment variables

- [ ] API pods have correct environment variables
  ```bash
  kubectl exec -n secapi <api-pod-name> -- env | grep -E "DATABASE_URL|REDIS_URL|ENVIRONMENT"
  ```
  Expected: Proper connection strings

### Secret Verification
- [ ] Secret is created
  ```bash
  kubectl get secret secapi-secrets -n secapi
  ```
  Expected: Secret exists (unless using existingSecret)

- [ ] Secret values are mounted (check for SECRET_KEY, etc.)
  ```bash
  kubectl exec -n secapi <api-pod-name> -- env | grep SECRET_KEY
  ```
  Expected: Secret key value set

---

## Persistence Tests

### PVCs Are Created and Bound
- [ ] PostgreSQL PVC is bound
  ```bash
  kubectl get pvc -n secapi | grep postgres
  ```
  Expected: STATUS: Bound

- [ ] Redis PVC is bound
  ```bash
  kubectl get pvc -n secapi | grep redis
  ```
  Expected: STATUS: Bound

- [ ] Scan cache PVC (if enabled)
  ```bash
  kubectl get pvc -n secapi | grep scan
  ```

### Data Survives Pod Deletion
- [ ] PostgreSQL data persists after pod restart
  ```bash
  # Count users before restart
  BEFORE=$(kubectl exec -n secapi <postgres-pod-name> -- \
    psql -U secapi -d secapi -tAc "SELECT COUNT(*) FROM users")

  # Restart postgres pod
  kubectl delete pod -n secapi -l app=postgres
  kubectl wait --for=condition=ready pod -l app=postgres -n secapi --timeout=120s

  # Count users after restart
  AFTER=$(kubectl exec -n secapi <postgres-pod-name> -- \
    psql -U secapi -d secapi -tAc "SELECT COUNT(*) FROM users")

  echo "Before: $BEFORE, After: $AFTER"
  ```
  Expected: Both counts equal

---

## Scaling Tests

### API Scaling
- [ ] Scale API replicas
  ```bash
  kubectl scale deployment secapi -n secapi --replicas=3
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=secapi -n secapi --timeout=120s
  kubectl get pods -n secapi -l app.kubernetes.io/name=secapi
  ```
  Expected: 3 pods running

- [ ] All API pods serve traffic
  ```bash
  for i in {1..10}; do
    curl -s $BASE_URL/health | jq -r '.status'
  done
  ```
  Expected: All requests return `healthy`

### Worker Scaling
- [ ] Scale worker replicas
  ```bash
  kubectl scale deployment secapi-worker -n secapi --replicas=2
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=worker -n secapi --timeout=120s
  kubectl get pods -n secapi -l app.kubernetes.io/component=worker
  ```
  Expected: 2 worker pods running

---

## Ingress Tests (if enabled)

### Ingress Resource Created
- [ ] Ingress exists
  ```bash
  kubectl get ingress -n secapi
  ```
  Expected: Ingress resource listed

### TLS/SSL
- [ ] TLS secret exists (if using cert-manager)
  ```bash
  kubectl get secret -n secapi | grep tls
  ```

- [ ] HTTPS works (if configured)
  ```bash
  curl -k https://<your-host>/health
  ```
  Expected: Healthy response

---

## Resource Limits

### Verify Resource Limits
- [ ] API pods have resource limits
  ```bash
  kubectl describe pod -n secapi -l app.kubernetes.io/name=secapi | grep -A 2 "Limits"
  ```
  Expected: CPU and memory limits defined

- [ ] Worker pods have resource limits
  ```bash
  kubectl describe pod -n secapi -l app.kubernetes.io/component=worker | grep -A 2 "Limits"
  ```

### Resource Usage Check
- [ ] Current resource usage
  ```bash
  kubectl top pods -n secapi
  ```
  Expected: Resources within limits

---

## Security Tests

### Pod Security Context
- [ ] API pods run as non-root
  ```bash
  kubectl exec -n secapi <api-pod-name> -- id
  ```
  Expected: UID not 0

- [ ] Read-only root filesystem (if enabled)
  ```bash
  kubectl exec -n secapi <api-pod-name> -- touch /tmp/test 2>&1
  ```
  Expected: Error if readOnlyRootFilesystem is true (should use emptyDir for /tmp)

### Network Policies (if enabled)
- [ ] Network policies exist
  ```bash
  kubectl get networkpolicy -n secapi
  ```

### RBAC
- [ ] ServiceAccount exists
  ```bash
  kubectl get sa -n secapi
  ```
  Expected: `secapi` serviceaccount

---

## Log Aggregation Tests

### API Logs
- [ ] View API logs
  ```bash
  kubectl logs -n secapi -l app.kubernetes.io/name=secapi --tail=50
  ```
  Expected: Application logs, no critical errors

### Worker Logs
- [ ] View worker logs
  ```bash
  kubectl logs -n secapi -l app.kubernetes.io/component=worker --tail=50
  ```
  Expected: Celery worker logs

### Error Detection
- [ ] Check for errors in all pods
  ```bash
  kubectl logs -n secapi --all-containers=true --tail=100 | grep -i "error\|critical\|exception" || echo "No errors found"
  ```

---

## Cleanup / Uninstall

### Remove Test Data
- [ ] Delete test scans via API
  ```bash
  SCAN_IDS=$(curl -s "$BASE_URL/api/v1/scans?page_size=100" \
    -H "Authorization: Bearer $API_KEY" | jq -r '.scans[].scan_id')

  for id in $SCAN_IDS; do
    curl -s -X DELETE "$BASE_URL/api/v1/scans/$id" \
      -H "Authorization: Bearer $API_KEY"
  done
  ```

### Uninstall Helm Release
- [ ] Uninstall the release
  ```bash
  helm uninstall secapi -n secapi
  ```
  Expected: Release uninstalled

- [ ] Verify release is gone
  ```bash
  helm list -n secapi
  ```
  Expected: Empty list

### Clean Up Remaining Resources
- [ ] Delete namespace (if desired)
  ```bash
  kubectl delete namespace secapi
  ```

- [ ] Delete PVCs for complete cleanup
  ```bash
  kubectl delete pvc -n secapi --all
  ```

---

## Upgrade Testing

### Helm Upgrade
- [ ] Upgrade with new values
  ```bash
  helm upgrade secapi helm/secapi \
    --namespace secapi \
    --values helm/secapi/values.yaml \
    --set replicaCount=3
  ```
  Expected: Release upgraded

- [ ] Verify new replica count
  ```bash
  kubectl get pods -n secapi -l app.kubernetes.io/name=secapi
  ```
  Expected: 3 replicas

### Rollback Test
- [ ] Rollback to previous version
  ```bash
  helm rollback secapi -n secapi
  ```
  Expected: Rollback successful

---

## Monitoring / Metrics (if using Prometheus)

### ServiceMonitor (if installed)
- [ ] ServiceMonitor exists
  ```bash
  kubectl get servicemonitor -n secapi
  ```

### Scrape Targets
- [ ] Metrics endpoint is accessible
  ```bash
  kubectl port-forward -n secapi svc/secapi 8000:8000 &
  curl -s http://localhost:8000/metrics | head -20
  kill %1
  ```

---

## Test Variables Reference

```bash
# Cluster
export KUBECONFIG="<path-to-kubeconfig>"
export NS="secapi"

# API
export BASE_URL="http://localhost:8000"  # or your ingress URL
export FLOWER_URL="http://localhost:5555"

# Test data
export API_KEY="<your_api_key>"
export SCAN_ID="<your_scan_id>"
export RESET_TOKEN="<your_reset_token>"
```

---

## Quick Test Script (Optional)

```bash
#!/bin/bash
set -e

export NS="secapi"
export BASE_URL="http://localhost:8000"

echo "=== SecAPI K8s Integration Test ==="

# Port forward
kubectl port-forward -n $NS svc/secapi 8000:8000 &
PF_PID=$!
sleep 5

trap "kill $PF_PID" EXIT

# Health check
echo "Testing health endpoint..."
curl -s $BASE_URL/health | jq .

# Register user
echo "Registering test user..."
RESP=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "quick-test@example.com"}')
echo $RESP | jq .
API_KEY=$(echo $RESP | jq -r '.api_key')

# Submit scan
echo "Submitting scan..."
SCAN_RESP=$(curl -s -X POST $BASE_URL/api/v1/scan/docker \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"image": "alpine:latest"}')
echo $SCAN_RESP | jq .
SCAN_ID=$(echo $SCAN_RESP | jq -r '.scan_id')

# Poll for completion
echo "Waiting for scan to complete..."
for i in {1..30}; do
  STATUS=$(curl -s $BASE_URL/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 5
done

echo "=== Tests Complete ==="
```
