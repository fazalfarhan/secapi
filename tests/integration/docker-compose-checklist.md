# Docker Compose Deployment Integration Test Checklist

**Base URL:** `http://localhost:8000`
**Flower URL:** `http://localhost:5555`

---

## Pre-Deployment Checks

### Environment Prerequisites
- [ ] Docker is installed and running (`docker --version`)
  ```bash
  docker --version
  ```
- [ ] Docker Compose is available (`docker compose version`)
  ```bash
  docker compose version
  ```
- [ ] No conflicting services on ports 5432, 6379, 8000, 5555
  ```bash
  lsof -i :5432 -i :6379 -i :8000 -i :5555 || echo "Ports available"
  ```
- [ ] Sufficient disk space (5GB+ recommended)
  ```bash
  df -h .
  ```

### Configuration
- [ ] `.env` file exists or defaults are acceptable
- [ ] `docker-compose.yml` is present and valid
  ```bash
  docker compose config
  ```

---

## Deployment

### Start Services
- [ ] Start all services
  ```bash
  docker compose up -d
  ```

### Verify Container Startup
- [ ] All containers are running
  ```bash
  docker compose ps
  ```
  Expected output: 5 containers (postgres, redis, api, celery_worker, flower) with status "running"

- [ ] Check API container logs
  ```bash
  docker compose logs api | tail -20
  ```
  Expected: `Application startup complete`

- [ ] Check Celery worker logs
  ```bash
  docker compose logs celery_worker | tail -20
  ```
  Expected: `celery@worker ready.`

- [ ] Check Flower logs
  ```bash
  docker compose logs flower | tail -20
  ```
  Expected: Flower running on port 5555

---

## Service Health Checks

### API Health Endpoint
- [ ] Root endpoint returns HTML
  ```bash
  curl -s http://localhost:8000/ | head -10
  ```
  Expected: HTML content containing SecAPI

- [ ] Health endpoint returns healthy status
  ```bash
  curl -s http://localhost:8000/health | jq .
  ```
  Expected: `{"status": "healthy", ...}`

- [ ] API v1 health endpoint
  ```bash
  curl -s http://localhost:8000/api/v1/health | jq .
  ```
  Expected: `{"status": "healthy", ...}`

### PostgreSQL Health
- [ ] PostgreSQL is accepting connections
  ```bash
  docker exec secapi-postgres pg_isready -U secapi
  ```
  Expected: `secapi:5432 - accepting connections`

- [ ] Database tables exist (alembic_version)
  ```bash
  docker exec secapi-postgres psql -U secapi -d secapi -c "\dt"
  ```
  Expected: List of tables including `users`, `scans`, `api_key_reset_tokens`

### Redis Health
- [ ] Redis is responding
  ```bash
  docker exec secapi-redis redis-cli ping
  ```
  Expected: `PONG`

### Flower (Celery Monitor) Health
- [ ] Flower UI is accessible
  ```bash
  curl -s http://localhost:5555 | grep -i "flower"
  ```
  Expected: HTML with Flower interface

- [ ] Flower shows connected workers
  ```bash
  curl -s http://localhost:5555/api/workers | jq .
  ```
  Expected: JSON with worker information

---

## API Endpoint Tests

### Authentication: User Registration
- [ ] Register a new user (save the returned `api_key` for subsequent tests!)
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' | jq .
  ```
  Expected: Response with `id`, `email`, `api_key`, `tier`, `created_at`

- [ ] Duplicate registration returns 409
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' | jq .
  ```
  Expected: `{"detail": "User with this email already exists"}`

**Save your API key for all subsequent requests:**
```bash
export API_KEY="<api_key_from_registration_response>"
```

### Authentication: API Key Reset Request
- [ ] Request reset token (check container logs for the token)
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/auth/reset-request \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' | jq .
  ```
  Expected: `{"message": "If the email exists, a reset link was sent"}`

- [ ] Retrieve reset token from logs (development mode only)
  ```bash
  docker compose logs api | grep "Reset token" | tail -1
  ```

### Authentication: API Key Reset Confirmation
- [ ] Confirm reset with token (replace `$RESET_TOKEN` from logs)
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/auth/reset-confirm \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "token": "'"$RESET_TOKEN"'"}' | jq .
  ```
  Expected: Response with new `api_key` and `message`

### Scans: Submit Docker Image Scan
- [ ] Submit a scan without API key returns 401
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -d '{"image": "nginx:alpine"}' | jq .
  ```
  Expected: `{"detail": "Not authenticated"}` or 401 status

- [ ] Submit a scan with valid API key
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "nginx:alpine"}' | jq .
  ```
  Expected: Response with `scan_id`, `status="queued"`, `check_status_url`

**Save the scan_id for subsequent tests:**
```bash
export SCAN_ID="<scan_id_from_response>"
```

- [ ] Submit scan with options
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "python:3.11-slim", "options": {"severity": "HIGH,CRITICAL"}}' | jq .
  ```
  Expected: Response with `scan_id`

### Scans: Check Scan Status
- [ ] Get scan status (JSON format - default)
  ```bash
  curl -s http://localhost:8000/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Status `pending`, `running`, or `completed`

- [ ] Get scan status (table format)
  ```bash
  curl -s http://localhost:8000/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY?format=table"
  ```
  Expected: Plain text table with scan results

- [ ] Access scan with different user returns 404
  ```bash
  # First register another user
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "another@example.com"}' | jq -r '.api_key' > /tmp/other_key.txt

  # Try to access original scan
  curl -s http://localhost:8000/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $(cat /tmp/other_key.txt)" | jq .
  ```
  Expected: `{"detail": "Scan not found"}`

- [ ] Access non-existent scan returns 404
  ```bash
  curl -s http://localhost:8000/api/v1/scans/00000000-0000-0000-0000-000000000000 \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: `{"detail": "Scan not found"}`

### Scans: List Scans
- [ ] List all scans for user
  ```bash
  curl -s "http://localhost:8000/api/v1/scans?page=1&page_size=10" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Response with `total`, `scans` array, `page`, `page_size`

- [ ] List scans with status filter
  ```bash
  curl -s "http://localhost:8000/api/v1/scans?status=completed" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Only completed scans

- [ ] List scans with type filter
  ```bash
  curl -s "http://localhost:8000/api/v1/scans?type=trivy" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Only trivy scans

- [ ] Paginate through scans
  ```bash
  curl -s "http://localhost:8000/api/v1/scans?page=1&page_size=5" \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: Response with pagination info

### Scans: Delete Scan
- [ ] Delete a completed/failed scan
  ```bash
  # Wait for a scan to complete, then delete
  curl -s -X DELETE http://localhost:8000/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" -w "\nHTTP Status: %{http_code}\n"
  ```
  Expected: HTTP 204, no content

- [ ] Cannot delete running/pending scan returns 400
  ```bash
  # Submit a new scan and try to delete immediately
  NEW_SCAN=$(curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "alpine:latest"}' | jq -r '.scan_id')

  curl -s -X DELETE http://localhost:8000/api/v1/scans/$NEW_SCAN \
    -H "Authorization: Bearer $API_KEY" | jq .
  ```
  Expected: `{"detail": "Cannot delete scan in progress"}`

---

## Celery Worker Verification

### Worker Status
- [ ] Worker is registered in Flower
  ```bash
  curl -s http://localhost:5555/api/workers | jq 'keys'
  ```
  Expected: Worker name(s) in response

- [ ] Worker is processing tasks (submit a scan first)
  ```bash
  # Submit a scan
  curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "node:20-alpine"}' > /dev/null

  # Check executed tasks
  sleep 2 && curl -s http://localhost:5555/api/tasks | jq '. | length'
  ```
  Expected: Tasks appear in the list

### Task Execution
- [ ] Scan completes successfully
  ```bash
  # Submit scan and poll for completion
  SCAN_ID=$(curl -s -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"image": "redis:7-alpine"}' | jq -r '.scan_id')

  for i in {1..30}; do
    STATUS=$(curl -s http://localhost:8000/api/v1/scans/$SCAN_ID \
      -H "Authorization: Bearer $API_KEY" | jq -r '.status')
    echo "Attempt $i: $STATUS"
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
      break
    fi
    sleep 5
  done
  ```
  Expected: Final status is `completed`

- [ ] Scan results contain vulnerability data
  ```bash
  curl -s http://localhost:8000/api/v1/scans/$SCAN_ID \
    -H "Authorization: Bearer $API_KEY" | jq '.results.summary'
  ```
  Expected: Summary with vulnerability counts (critical, high, medium, low)

---

## Database Connectivity

### Connection Pool
- [ ] API can connect to database
  ```bash
  docker exec secapi-api python -c "
  import asyncio
  from app.db.session import get_db
  async def test():
      async for db in get_db():
          print('Database connection successful')
          break
  asyncio.run(test())
  "
  ```
  Expected: `Database connection successful`

### Data Persistence
- [ ] User data persists across container restarts
  ```bash
  # Register a user
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "persist@test.com"}' | jq -r '.id' > /tmp/user_id.txt

  # Restart API
  docker compose restart api && sleep 5

  # Verify user still exists
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "persist@test.com"}' | jq .
  ```
  Expected: 409 Conflict - user already exists

---

## Error Handling

### Invalid API Key
- [ ] Requests with invalid API key return 401
  ```bash
  curl -s http://localhost:8000/api/v1/scans \
    -H "Authorization: Bearer invalid_key_123" | jq .
  ```
  Expected: 401 Unauthorized

### Missing Authorization Header
- [ ] Requests without auth header return 401
  ```bash
  curl -s http://localhost:8000/api/v1/scans | jq .
  ```
  Expected: 401 Unauthorized

### Malformed Requests
- [ ] Invalid JSON returns 422
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"invalid": data}' | jq .
  ```
  Expected: 422 Validation Error

### Rate Limiting (if enabled)
- [ ] Exceeding rate limit returns 429
  ```bash
  for i in {1..150}; do
    curl -s http://localhost:8000/api/v1/scans \
      -H "Authorization: Bearer $API_KEY" -w "%{http_code}\n" -o /dev/null
  done | grep 429
  ```
  Expected: HTTP 429 after threshold (default: 100 req/hour)

---

## Cleanup

### Remove Test Data
- [ ] Delete test scans (if desired for cleanup)
  ```bash
  # List and delete each scan
  SCAN_IDS=$(curl -s "http://localhost:8000/api/v1/scans?page_size=100" \
    -H "Authorization: Bearer $API_KEY" | jq -r '.scans[].scan_id')

  for id in $SCAN_IDS; do
    curl -s -X DELETE "http://localhost:8000/api/v1/scans/$id" \
      -H "Authorization: Bearer $API_KEY"
  done
  ```

### Stop Services
- [ ] Stop all containers
  ```bash
  docker compose down
  ```

### Remove Volumes (Complete Cleanup)
- [ ] Remove all data volumes
  ```bash
  docker compose down -v
  ```

### Verify Cleanup
- [ ] No containers running
  ```bash
  docker compose ps
  ```
  Expected: Empty list

---

## Additional Tests

### OpenAPI Documentation
- [ ] Swagger UI is accessible
  ```bash
  curl -s http://localhost:8000/docs | grep -i swagger
  ```
  Expected: HTML with Swagger UI

- [ ] OpenAPI schema is valid
  ```bash
  curl -s http://localhost:8000/api/v1/openapi.json | jq '.openapi'
  ```
  Expected: OpenAPI version string

### Container Logs Review
- [ ] No critical errors in logs
  ```bash
  docker compose logs --tail=100 | grep -i "error\|critical\|exception" || echo "No errors found"
  ```

### Resource Usage
- [ ] Check container resource usage
  ```bash
  docker stats --no-stream $(docker compose ps -q)
  ```
  Expected: Reasonable CPU/memory usage

---

## Test Variables Reference

```bash
# Set these for manual testing
export BASE_URL="http://localhost:8000"
export FLOWER_URL="http://localhost:5555"
export API_KEY="<your_api_key>"
export SCAN_ID="<your_scan_id>"
export RESET_TOKEN="<your_reset_token>"
```
