# Phase 1: Foundation & Core Infrastructure (Days 1-3)

**Goal**: Set up project foundation, development environment, and core infrastructure components.

## Overview

This phase establishes the technical foundation for SecAPI. You'll set up the project structure, development environment, database, and basic FastAPI application with authentication.

## Tasks Checklist

### 1.1 Project Setup (Day 1 - Morning)

- [ ] Create base project structure
- [ ] Set up Python 3.11+ virtual environment
- [ ] Create `requirements.txt` and `requirements-dev.txt`
- [ ] Set up pre-commit hooks
- [ ] Configure `.gitignore`
- [ ] Create MIT LICENSE file
- [ ] Set up `pyproject.toml` for project metadata

**Files to Create:**
```
secapi/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── LICENSE
└── .pre-commit-config.yaml
```

**Deliverables:**
- Working Python environment with all dependencies
- Git repository initialized with proper ignore rules
- Pre-commit hooks configured (black, ruff, mypy)

### 1.2 Database Setup (Day 1 - Afternoon)

- [ ] Create SQLAlchemy models (User, Scan, ApiUsage, RateLimit)
- [ ] Set up Alembic for migrations
- [ ] Create initial migration
- [ ] Create database session management
- [ ] Write model tests

**Files to Create:**
```
app/
├── db/
│   ├── __init__.py
│   ├── base.py           # Base declarative model
│   ├── session.py        # Async session factory
│   └── models.py         # SQLAlchemy models
└── core/
    └── config.py         # Settings management
```

**Database Schema:**
- `users` table (id, email, api_key_hash, tier, created_at, updated_at)
- `scans` table (id, user_id, scan_type, status, input_data, results, error_message, timestamps)
- `api_usage` table (id, user_id, endpoint, method, status_code, response_time_ms, timestamp)
- `rate_limits` table (user_id, scans_count, period_start, last_reset)

**Deliverables:**
- Working database models with proper relationships
- Alembic configured with initial migration
- Async database session management
- Tests for all models

### 1.3 Docker Infrastructure (Day 2 - Morning)

- [ ] Create `Dockerfile` for the application
- [ ] Create `docker-compose.yml` for development
- [ ] Set up PostgreSQL service
- [ ] Set up Redis service
- [ ] Configure volumes and networks
- [ ] Test Docker build and compose

**Files to Create:**
```
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

**Services to Configure:**
- PostgreSQL 15-alpine
- Redis 7-alpine
- API service (hot-reload enabled)

**Deliverables:**
- Working Docker Compose setup
- All services running and communicating
- Environment properly configured

### 1.4 Core Configuration & Security (Day 2 - Afternoon)

- [ ] Implement Pydantic Settings for configuration
- [ ] Set up API key generation and validation
- [ ] Create authentication dependency
- [ ] Implement structured logging with structlog
- [ ] Set up CORS middleware
- [ ] Create error handlers

**Files to Create:**
```
app/core/
├── config.py         # Pydantic settings
├── security.py       # API key helpers, auth
├── logging.py        # Structured logging setup
└── dependencies.py   # FastAPI dependencies
```

**Configuration Variables:**
```python
DATABASE_URL, REDIS_URL, CELERY_BROKER_URL
ENVIRONMENT, SECRET_KEY, API_BASE_URL
ALLOWED_ORIGINS, RATE_LIMIT_ENABLED
```

**Deliverables:**
- Centralized configuration management
- API key generation/verification functions
- Authentication middleware
- Structured JSON logging

### 1.5 Base FastAPI Application (Day 3)

- [ ] Create main FastAPI application
- [ ] Set up API router structure
- [ ] Create health check endpoint
- [ ] Create Pydantic schemas for common types
- [ ] Write basic API tests
- [ ] Set up OpenAPI documentation customization

**Files to Create:**
```
app/
├── main.py              # FastAPI app factory
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── router.py    # API v1 router
└── schemas/
    ├── __init__.py
    ├── common.py        # Common schemas
    └── user.py          # User schemas
```

**Endpoints to Create:**
- `GET /` - Root endpoint with API info
- `GET /health` - Health check (DB, Redis status)
- `GET /api/v1/` - API v1 info

**Deliverables:**
- Working FastAPI application
- Health check endpoint
- Auto-generated OpenAPI docs at /docs
- Basic test suite

## Acceptance Criteria

Phase 1 is complete when:

1. ✅ `docker-compose up -d` starts all services successfully
2. ✅ Health check endpoint returns `{"status": "healthy", "database": "connected", "redis": "connected"}`
3. ✅ Database migrations can be applied and rolled back
4. ✅ API keys can be generated and validated
5. ✅ Structured logs are emitted in JSON format
6. ✅ All tests pass: `pytest` (target: basic coverage)
7. ✅ Pre-commit hooks work: commit triggers linting/formatting

## Commands for Phase 1

```bash
# Initial setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Pre-commit setup
pre-commit install

# Database
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Docker
docker-compose build
docker-compose up -d
docker-compose logs -f

# Testing
pytest --cov=app --cov-report=html

# Code quality
black app/ tests/
ruff check app/ tests/
mypy app/
```

## Notes

- Keep database schema simple initially - add fields as needed
- Don't worry about Celery workers yet (Phase 2)
- Focus on type hints and async patterns throughout
- Write tests as you build (TDD approach)

## Next Phase

After completing Phase 1, proceed to **Phase 1-1: Trivy Scanner Integration** to implement the first security scanner.
