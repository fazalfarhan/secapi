# SecAPI

Open-source security scanning API platform. Self-hostable alternative to commercial security platforms.

## What It Does

- **Unified REST API** for Trivy security scans
- **Async scanning** via Celery workers - submit and poll for results
- **Multi-user support** with API keys for team collaboration

## Quick Start

```bash
# 1. Clone and start
git clone https://github.com/yourusername/secapi.git
cd secapi
docker-compose up -d

# 2. Register (save the API key - shown only once)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'

# 3. Submit a scan
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"image": "nginx:latest"}'

# 4. Check results
curl http://localhost:8000/api/v1/scans/{scan_id} \
  -H "X-API-Key: YOUR_API_KEY"
```

Services:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitor): http://localhost:5555

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user, get API key |
| POST | `/api/v1/scan/docker` | Submit Docker image scan |
| GET | `/api/v1/scans` | List your scans (paginated) |
| GET | `/api/v1/scans/{scan_id}` | Get scan status/results |
| DELETE | `/api/v1/scans/{scan_id}` | Delete scan record |
| GET | `/health` | Health check |

Scan statuses: `pending` → `running` → `completed` or `failed`

## Multi-User Benefits

- **API key per user** - Track who initiated which scan
- **Scan isolation** - Each user sees only their own scans
- **Tier-based rate limiting** - Fair resource allocation (free/pro/enterprise)
- **Audit trail** - Complete history for compliance

Instead of each developer running Trivy locally with inconsistent configs, SecAPI provides centralized, standardized scanning for the entire team.

## Configuration

Essential environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis for caching |
| `CELERY_BROKER_URL` | Celery message broker |
| `SECRET_KEY` | JWT signing secret (required) |
| `ENVIRONMENT` | `development` or `production` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting (default: true) |

## CI/CD Example

```yaml
# GitHub Actions
- name: Security Scan
  run: |
    SCAN_ID=$(curl -X POST $SECAPI_URL/api/v1/scan/docker \
      -H "X-API-Key: $SECAPI_KEY" \
      -d '{"image": "myapp:${{ github.sha }}"}' | jq -r '.scan_id')
    sleep 30
    curl $SECAPI_URL/api/v1/scans/$SCAN_ID -H "X-API-Key: $SECAPI_KEY" | jq '.results'
```

## License

MIT
