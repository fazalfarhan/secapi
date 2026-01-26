# Phase 1-1: Trivy Scanner Integration (Days 4-5)

**Goal**: Implement the first security scanner - Trivy for Docker image vulnerability scanning.

## Overview

This phase implements the Trivy scanner, which is the core scanner for SecAPI. You'll create the base scanner interface, implement Trivy integration, create API endpoints, and set up Celery for async scanning.

## Tasks Checklist

### 1.1 Base Scanner Interface (Day 4 - Morning)

- [ ] Create `BaseScanner` abstract class
- [ ] Define scanner interface methods
- [ ] Create unified result format models
- [ ] Implement severity normalization
- [ ] Create scanner exceptions

**Files to Create:**
```
app/scanners/
├── __init__.py
├── base.py           # BaseScanner abstract class
└── exceptions.py     # Scanner-specific exceptions
```

**BaseScanner Interface:**
```python
class BaseScanner(ABC):
    @abstractmethod
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scan and return normalized results"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input parameters before scanning"""
        pass

    @abstractmethod
    async def scan_async(self, input_data: Dict[str, Any]) -> str:
        """Queue scan for async execution, returns scan_id"""
        pass

    def normalize_severity(self, severity: str) -> str:
        """Normalize severity levels across scanners"""
        pass
```

**Unified Result Format:**
```python
{
    "scan_id": "uuid",
    "scan_type": "docker",
    "status": "completed",
    "metadata": {
        "scanned_at": "ISO8601 timestamp",
        "scanner_version": "trivy-0.48.0",
        "scan_duration": "2.3s"
    },
    "summary": {
        "critical": 0,
        "high": 2,
        "medium": 5,
        "low": 10,
        "info": 3
    },
    "findings": [...]
}
```

**Deliverables:**
- Base scanner class with type hints
- Scanner exception classes
- Unified result format schemas
- Tests for base scanner functionality

### 1.2 Trivy Scanner Implementation (Day 4 - Afternoon)

- [ ] Install Trivy in Docker image
- [ ] Implement `TrivyScanner` class
- [ ] Add subprocess execution with timeout
- [ ] Parse Trivy JSON output
- [ ] Normalize to unified format
- [ ] Add error handling for Trivy failures

**Files to Create:**
```
app/scanners/
└── trivy.py          # TrivyScanner implementation
```

**TrivyScanner Methods:**
```python
class TrivyScanner(BaseScanner):
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Trivy scan on Docker image"""
        # 1. Validate input
        # 2. Build Trivy command
        # 3. Execute subprocess with timeout
        # 4. Parse JSON output
        # 5. Normalize to unified format
        # 6. Return results

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate Docker image name"""
        # Check for valid image format
        # Prevent shell injection

    def _normalize_output(self, raw: Dict, image: str) -> Dict[str, Any]:
        """Convert Trivy output to unified format"""
        # Map Trivy fields to unified format
        # Count severities
        # Extract findings
```

**Trivy Command:**
```bash
trivy image --format json --quiet --severity CRITICAL,HIGH,MEDIUM,LOW <image>
```

**Deliverables:**
- Working Trivy scanner implementation
- Input validation (prevent shell injection)
- Output parsing and normalization
- Error handling for timeouts and failures
- Comprehensive tests

### 1.3 Celery Task Queue Setup (Day 5 - Morning)

- [ ] Create Celery app configuration
- [ ] Implement Celery worker
- [ ] Create scan task
- [ ] Add task status tracking
- [ ] Configure result backend
- [ ] Update Docker Compose

**Files to Create:**
```
app/
├── worker.py          # Celery worker entry point
├── tasks/
│   ├── __init__.py
│   └── scan.py        # Celery scan tasks
└── core/
    └── celery.py      # Celery app factory
```

**Celery Task:**
```python
@celery_app.task(bind=True)
def execute_trivy_scan(self, scan_id: str, image: str, options: Dict):
    """Execute Trivy scan asynchronously"""
    # 1. Update scan status to "scanning"
    # 2. Execute scan
    # 3. Update scan status and results
    # 4. Handle errors
```

**Docker Compose Update:**
Add `worker` service and optional `flower` for monitoring.

**Deliverables:**
- Celery worker configured with Redis broker
- Async scan task implementation
- Task status tracking in database
- Worker service in Docker Compose

### 1.4 Docker Scan API Endpoints (Day 5 - Afternoon)

- [ ] Create Pydantic request/response schemas
- [ ] Implement `POST /api/v1/scan/docker` endpoint
- [ ] Implement `GET /api/v1/scans/{scan_id}` endpoint
- [ ] Add request validation
- [ ] Implement caching layer
- [ ] Write API tests

**Files to Create:**
```
app/api/v1/endpoints/
├── __init__.py
├── docker.py         # Docker scan endpoints
└── scans.py          # Scan result endpoints

app/schemas/
└── scan.py           # Scan-related schemas
```

**Endpoints:**
```http
# Queue Docker scan
POST /api/v1/scan/docker
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "image": "nginx:latest",
  "options": {
    "severity": ["CRITICAL", "HIGH"],
    "scanners": ["vulnerabilities"]
  }
}

Response 202:
{
  "scan_id": "uuid",
  "status": "queued",
  "check_status_url": "/api/v1/scans/{scan_id}"
}

# Get scan results
GET /api/v1/scans/{scan_id}
Authorization: Bearer <api_key>

Response 200:
{
  "scan_id": "uuid",
  "status": "completed",
  "scan_type": "docker",
  "created_at": "2025-01-25T10:30:00Z",
  "completed_at": "2025-01-25T10:30:45Z",
  "results": {...}
}
```

**Deliverables:**
- Working scan endpoints
- Request/response validation with Pydantic
- Async task execution via Celery
- Caching layer with Redis
- Comprehensive API tests

### 1.5 Testing & Integration (Day 5 - Late Afternoon)

- [ ] Test full scan flow end-to-end
- [ ] Test error scenarios (invalid image, timeout)
- [ ] Test caching behavior
- [ ] Verify Celery task execution
- [ ] Update Docker Compose documentation
- [ ] Write API usage examples

**Testing Checklist:**
- Valid scan returns scan_id
- Status endpoint returns correct states
- Completed scan contains normalized results
- Invalid images return proper errors
- Timeout handling works
- Cache hits work correctly
- Celery worker processes tasks
- Database records are created

**Deliverables:**
- Full test coverage for Docker scanning
- Integration tests
- API usage documentation
- Updated README with examples

## Acceptance Criteria

Phase 1-1 is complete when:

1. ✅ `POST /api/v1/scan/docker` accepts valid requests
2. ✅ Celery worker processes scan asynchronously
3. ✅ `GET /api/v1/scans/{scan_id}` returns results
4. ✅ Results are in unified format with normalized severity
5. ✅ Cache works (identical scans hit cache)
6. ✅ Error handling works (invalid images, timeouts)
7. ✅ All tests pass with 80%+ coverage
8. ✅ Trivy is installed and working in Docker

## Commands for Phase 1-1

```bash
# Install Trivy locally for testing
brew install trivy  # macOS
# or use Docker image

# Test Trivy directly
trivy image nginx:latest

# Run Celery worker
celery -A app.worker worker --loglevel=info

# Run with Docker Compose
docker-compose up -d worker
docker-compose logs -f worker

# Test API
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:latest"}'

# Run tests
pytest tests/test_scanners/test_trivy.py -v
pytest tests/test_api/test_docker.py -v
```

## API Example

```bash
# 1. Start services
docker-compose up -d

# 2. Generate API key (or use development key)
python -c "from app.core.security import generate_api_key; print(generate_api_key()[0])"

# 3. Queue scan
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Authorization: Bearer sk_test_..." \
  -H "Content-Type: application/json" \
  -d '{
    "image": "nginx:1.24",
    "options": {
      "severity": ["CRITICAL", "HIGH"]
    }
  }'

# Response:
# {"scan_id": "550e8400-...", "status": "queued", ...}

# 4. Check status
curl http://localhost:8000/api/v1/scans/550e8400-... \
  -H "Authorization: Bearer sk_test_..."

# 5. Get results when complete
```

## Notes

- Start with synchronous scanning, then convert to async
- Handle Docker images that don't exist
- Set reasonable timeout (5 minutes default)
- Cache based on image tag (not just name)
- Log all scan attempts for audit

## Next Phase

After completing Phase 1-1, proceed to **Phase 1-2: Checkov Scanner Integration** to add Infrastructure-as-Code scanning.
