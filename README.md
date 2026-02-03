# SecAPI

Open-source security scanning API platform. Self-hostable alternative to commercial security platforms.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (CLI/CI/CD)                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP REST
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Auth      │  │  Scan API    │  │     Health Check      │  │
│  │  (API Keys)  │  │  (Endpoints) │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
│         │                  │                                     │
│         ▼                  ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL (User + Scan Data)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Celery Task
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Redis (Broker)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Celery Worker Process                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Scanner Layer                          │  │
│  │  ┌─────────┐    ┌─────────┐    ┌──────────────────┐     │  │
│  │  │ Trivy   │    │ Grype   │    │   (more soon)     │     │  │
│  │  │ Scanner │    │ Scanner │    │                   │     │  │
│  │  └────┬────┘    └────┬────┘    └──────────────────┘     │  │
│  └───────┴─────────────┴────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│                    Store Results → DB                          │
└─────────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Client submits scan → API creates scan record (status: `pending`)
2. API queues Celery task with scan details
3. Celery worker picks up task, executes scanner (Trivy)
4. Worker updates DB with results (status: `completed`)
5. Client polls for results → API returns from DB

## What It Does

- **Unified REST API** for Trivy security scans
- **Async scanning** via Celery workers - submit and poll for results
- **Multi-user support** with API keys for team collaboration

## Quick Start

```bash
# 1. Clone and start
git clone https://github.com/fazalfarhan/secapi.git
cd secapi
cp .env.dev .env
docker-compose up -d

# 2. Register (save the API key - shown only once)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'

# 3. Submit a scan
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"image": "nginx:latest"}'

# 4. Check results (JSON format)
curl http://localhost:8000/api/v1/scans/{scan_id}?format=json \
  -H "Authorization: Bearer YOUR_API_KEY"

# 5. Check results (table format)
curl http://localhost:8000/api/v1/scans/{scan_id}?format=table \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Services:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitor): http://localhost:5555

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user, get API key |
| POST | `/api/v1/auth/reset-request` | Request API key reset |
| POST | `/api/v1/auth/reset-confirm` | Confirm reset with token, get new key |
| POST | `/api/v1/scan/docker` | Submit Docker image scan |
| GET | `/api/v1/scans` | List your scans (paginated) |
| GET | `/api/v1/scans/{scan_id}` | Get scan status/results |
| GET | `/api/v1/scans/{scan_id}?format=table` | Get results in table format |
| DELETE | `/api/v1/scans/{scan_id}` | Delete scan record |
| GET | `/health` | Health check |

Scan statuses: `pending` → `running` → `completed` or `failed`

## API Key Reset

Lost your API key? Reset it securely:

```bash
# 1. Request reset
curl -X POST http://localhost:8000/api/v1/auth/reset-request \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'

# 2. Get token (development: check logs, production: check email)
# Development: docker-compose logs api | grep reset_token
# Production: check your email inbox

# 3. Confirm reset
curl -X POST http://localhost:8000/api/v1/auth/reset-confirm \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "token": "<token_from_logs_or_email>"}'

# Response: {"api_key": "secapi_new_key", "message": "API key regenerated"}
```

- **Development mode**: Token logged to console
- **Production mode**: Token sent via email
- Tokens expire in 15 minutes and are one-time use only

## Supported Scanners

| Scanner | Status | Use Case |
|---------|--------|----------|
| Trivy |  Supported | Container/FS vulnerabilities, misconfigurations |
| Grype |  Coming Soon | Container vulnerability scanning |

## Authentication

All authenticated endpoints use Bearer token authentication:

```bash
# Correct
-H "Authorization: Bearer YOUR_API_KEY"

# Incorrect (deprecated)
-H "X-API-Key: YOUR_API_KEY"
```

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

## Kubernetes Deployment

```bash
# 1. Build image
docker build -t secapi:latest .

# 2. Load into cluster (Colima/Kind)
docker save secapi:latest | colima load -

# 3. Install Helm chart
helm install secapi ./helm/secapi \
  --set postgres.postgresPassword=changeme

# 4. Port forward
kubectl port-forward svc/secapi-api 8000:8000 -n secapi
```

See [helm/secapi/README.md](helm/secapi/README.md) for full documentation including production setup with external databases and SMTP.

## CI/CD Example

```yaml
# GitHub Actions
- name: Security Scan
  run: |
    SCAN_ID=$(curl -X POST $SECAPI_URL/api/v1/scan/docker \
      -H "Authorization: Bearer $SECAPI_KEY" \
      -H "Content-Type: application/json" \
      -d '{"image": "myapp:${{ github.sha }}"}' | jq -r '.scan_id')
    sleep 30
    curl "$SECAPI_URL/api/v1/scans/$SCAN_ID?format=json" \
      -H "Authorization: Bearer $SECAPI_KEY" | jq '.results'
```

## License

MIT
