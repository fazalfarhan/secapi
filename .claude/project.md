# SecAPI Skill - Security Scanning API Platform

## Project Overview

**SecAPI** is an open-source, API-first security scanning platform that wraps industry-standard security tools (Trivy, Checkov, TruffleHog, etc.) into a unified REST API. It provides developers with simple HTTP endpoints for vulnerability scanning, secrets detection, and infrastructure-as-code (IaC) security checks.

**Core Philosophy**: 
- Open source first (MIT License)
- Self-hostable for free
- Optional managed service for convenience
- Developer-focused (API-first, not UI-first)
- DevSecOps best practices showcase

**Primary Goal**: Build portfolio demonstrating DevSecOps expertise while creating genuinely useful tooling for the developer community.

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, auto-generated OpenAPI docs)
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Task Queue**: Celery + Redis (for async scanning)

### Security Tools (Wrapped)
- **Trivy** - Container & dependency vulnerability scanning (PRIMARY)
- **Checkov** - Infrastructure-as-Code security scanning
- **TruffleHog** - Secrets detection in Git repositories
- **Bandit** - Python code security analysis
- **Safety** - Python dependency vulnerability checking
- **Semgrep** - Code pattern matching for security issues

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Deployment**: Docker-based (Railway, Render, VPS, AWS) GKE , kubernetes
- **CI/CD**: GitHub Actions, Gitlab CICD
- **Monitoring**: Prometheus + Grafana (optional)
- **Logging**: Structured JSON logging

### Testing
- **Framework**: pytest + pytest-asyncio
- **Coverage**: pytest-cov (target: 80%+)
- **Load Testing**: locust
- **Security Testing**: bandit, safety

---

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                      Client/User                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Endpoints (/scan/docker, /scan/iac, etc.)  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Authentication & Rate Limiting                   │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌──────────┐
    │  Redis  │   │  Celery │   │PostgreSQL│
    │ (Cache) │   │ (Queue) │   │ (Results)│
    └─────────┘   └────┬────┘   └──────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Scanner Workers│
              │ - Trivy        │
              │ - Checkov      │
              │ - TruffleHog   │
              └────────────────┘
```

### Component Responsibilities

**API Layer** (`app/api/`)
- REST endpoint definitions
- Request validation (Pydantic models)
- Response formatting
- Error handling
- API key authentication

**Service Layer** (`app/services/`)
- Business logic
- Scanner orchestration
- Result parsing & normalization
- Cache management

**Scanner Layer** (`app/scanners/`)
- Individual scanner implementations
- Subprocess execution of security tools
- Output parsing to unified format
- Error handling per scanner

**Database Layer** (`app/db/`)
- SQLAlchemy models
- Database session management
- Scan result storage
- Query utilities

---

## API Design

### Core Endpoints

#### 1. Container Scanning
```http
POST /api/v1/scan/docker
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "image": "nginx:latest",
  "options": {
    "severity": ["CRITICAL", "HIGH"],
    "scanners": ["vulnerabilities", "secrets"],
    "format": "json"
  }
}

Response 202 Accepted:
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "check_status_url": "/api/v1/scans/550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. Infrastructure-as-Code Scanning
```http
POST /api/v1/scan/iac
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "type": "terraform",
  "content": "resource \"aws_s3_bucket\" \"example\" {...}",
  "policies": ["cis-aws", "custom-policy-123"]
}

Response 200 OK:
{
  "scan_id": "660e8400-e29b-41d4-a716-446655440001",
  "findings": [
    {
      "severity": "HIGH",
      "check_id": "CKV_AWS_18",
      "description": "S3 bucket should have access logging enabled",
      "resource": "aws_s3_bucket.example",
      "file": "main.tf",
      "line": 5
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 5
  }
}
```

#### 3. Secrets Detection
```http
POST /api/v1/scan/secrets
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "source": "git",
  "repository": "https://github.com/user/repo",
  "branch": "main"
}

Response 202 Accepted:
{
  "scan_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "scanning",
  "estimated_time": "30s"
}
```

#### 4. Get Scan Results
```http
GET /api/v1/scans/{scan_id}
Authorization: Bearer <api_key>

Response 200 OK:
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "scan_type": "docker",
  "created_at": "2025-01-25T10:30:00Z",
  "completed_at": "2025-01-25T10:30:45Z",
  "results": {
    "image": "nginx:latest",
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 8,
      "low": 15
    },
    "details": [...]
  }
}
```

### Unified Response Format

All scanners return results in a normalized format:
```json
{
  "scan_id": "uuid",
  "scan_type": "docker|iac|secrets|code",
  "status": "completed|failed|scanning",
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
  "findings": [
    {
      "id": "CVE-2024-1234",
      "severity": "HIGH",
      "title": "Buffer overflow in libssl",
      "description": "...",
      "affected_component": "libssl 1.1.1",
      "fixed_version": "1.1.1w",
      "references": ["https://cve.mitre.org/..."]
    }
  ]
}
```

---

## Database Schema

### Core Tables
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'free', -- free, starter, pro, business
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scans table
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    scan_type VARCHAR(50) NOT NULL, -- docker, iac, secrets, code
    status VARCHAR(50) DEFAULT 'queued', -- queued, scanning, completed, failed
    input_data JSONB NOT NULL, -- Original request
    results JSONB, -- Scan results
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    scan_duration_ms INTEGER,
    INDEX idx_user_scans (user_id, created_at DESC),
    INDEX idx_scan_type (scan_type),
    INDEX idx_status (status)
);

-- API usage tracking
CREATE TABLE api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_usage (user_id, timestamp DESC)
);

-- Rate limiting
CREATE TABLE rate_limits (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    scans_count INTEGER DEFAULT 0,
    period_start TIMESTAMP DEFAULT NOW(),
    last_reset TIMESTAMP DEFAULT NOW()
);
```

---

## Caching Strategy

### Redis Cache Keys
```python
# Scan result cache (24 hours)
cache_key = f"scan:{scan_type}:{hash(input_params)}"
# Example: "scan:docker:sha256:abc123..."

# Rate limiting (per hour)
rate_limit_key = f"ratelimit:{user_id}:{hour_bucket}"
# Example: "ratelimit:user-123:2025-01-25-10"

# API key validation (5 minutes)
api_key_cache = f"apikey:{api_key_hash}"
```

### Cache Invalidation

- Scan results: 24 hours (configurable per tier)
- Rate limits: Reset hourly
- API keys: Invalidate on user update

---

## Scanner Implementation

### Base Scanner Interface
```python
# app/scanners/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseScanner(ABC):
    """Base class for all security scanners"""
    
    @abstractmethod
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scan and return normalized results
        
        Args:
            input_data: Scanner-specific input parameters
            
        Returns:
            Normalized scan results following unified format
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input parameters before scanning"""
        pass
    
    def normalize_severity(self, severity: str) -> str:
        """Normalize severity levels across scanners"""
        severity_map = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "INFO": "info"
        }
        return severity_map.get(severity.upper(), "unknown")
```

### Trivy Scanner Example
```python
# app/scanners/trivy.py
import subprocess
import json
from typing import Dict, Any
from .base import BaseScanner

class TrivyScanner(BaseScanner):
    """Docker image vulnerability scanner using Trivy"""
    
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        image = input_data["image"]
        
        # Execute Trivy
        cmd = [
            "trivy", "image",
            "--format", "json",
            "--quiet",
            image
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise ScannerError(f"Trivy failed: {result.stderr}")
        
        # Parse and normalize output
        raw_output = json.loads(result.stdout)
        return self._normalize_output(raw_output, image)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "image" in input_data and len(input_data["image"]) > 0
    
    def _normalize_output(self, raw: Dict, image: str) -> Dict[str, Any]:
        """Convert Trivy output to unified format"""
        findings = []
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for result in raw.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                severity = self.normalize_severity(vuln["Severity"])
                summary[severity] += 1
                
                findings.append({
                    "id": vuln.get("VulnerabilityID"),
                    "severity": severity.upper(),
                    "title": vuln.get("Title", ""),
                    "description": vuln.get("Description", ""),
                    "affected_component": vuln.get("PkgName"),
                    "installed_version": vuln.get("InstalledVersion"),
                    "fixed_version": vuln.get("FixedVersion"),
                    "references": vuln.get("References", [])
                })
        
        return {
            "image": image,
            "summary": summary,
            "findings": findings
        }
```

---

## Deployment Configurations

### Docker Compose (Development & Self-Hosting)
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/secapi
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - ENVIRONMENT=development
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker socket for image scanning
      - ./app:/app/app  # Hot reload in dev
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/secapi
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - trivy_cache:/root/.cache/trivy
    depends_on:
      - db
      - redis
    command: celery -A app.worker worker --loglevel=info

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: secapi
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Optional: Flower for Celery monitoring
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - worker
    command: celery -A app.worker flower --port=5555

volumes:
  postgres_data:
  redis_data:
  trivy_cache:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install Checkov
RUN pip install checkov

# Install TruffleHog
RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt
```
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Cache & Queue
redis==5.0.1
celery==5.3.4

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Utilities
httpx==0.26.0
aiofiles==23.2.1
python-dotenv==1.0.0

# Monitoring & Logging
prometheus-client==0.19.0
structlog==24.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
faker==22.0.0

# Code quality
black==24.1.1
ruff==0.1.14
mypy==1.8.0
bandit==1.7.6
safety==3.0.1
```

---

## Self-Hosting Documentation

### Quick Start (5 minutes)
```bash
# Clone repository
git clone https://github.com/yourusername/secapi.git
cd secapi

# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for local dev)
# nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Environment Variables
```bash
# .env.example

# Database
DATABASE_URL=postgresql://postgres:password@db:5432/secapi

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# Application
ENVIRONMENT=production  # development, staging, production
SECRET_KEY=your-secret-key-here-change-me
API_BASE_URL=https://api.yourdomain.com

# Security
ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000
RATE_LIMIT_ENABLED=true

# Scanning
TRIVY_CACHE_DIR=/root/.cache/trivy
MAX_SCAN_TIMEOUT=300  # seconds
ENABLE_DOCKER_SCAN=true
ENABLE_IAC_SCAN=true
ENABLE_SECRETS_SCAN=true

# Tiers & Limits (per month)
FREE_TIER_SCANS=100
STARTER_TIER_SCANS=5000
PRO_TIER_SCANS=50000
BUSINESS_TIER_SCANS=500000

# Optional: Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=false
```

### Production Deployment (VPS)
```bash
# On your VPS (Ubuntu 22.04)

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone & configure
git clone https://github.com/yourusername/secapi.git
cd secapi
cp .env.example .env
nano .env  # Set production values

# Generate secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env as SECRET_KEY

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d

# Setup nginx reverse proxy (optional)
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/secapi

# Add SSL
sudo certbot --nginx -d api.yourdomain.com
```

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/secapi

upstream secapi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://secapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Managed Service Strategy

### Pricing Tiers
```python
# app/models/tiers.py

TIERS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "scans_per_month": 100,
        "rate_limit_per_hour": 10,
        "cache_ttl": 3600,  # 1 hour
        "features": [
            "All scan types",
            "Basic support (GitHub Discussions)",
            "24-hour scan history"
        ]
    },
    "starter": {
        "name": "Starter",
        "price_monthly": 19,
        "scans_per_month": 5000,
        "rate_limit_per_hour": 100,
        "cache_ttl": 86400,  # 24 hours
        "features": [
            "All scan types",
            "Email support",
            "30-day scan history",
            "Webhook notifications",
            "Custom policies"
        ]
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 49,
        "scans_per_month": 50000,
        "rate_limit_per_hour": 500,
        "cache_ttl": 86400,
        "features": [
            "All Starter features",
            "Priority scanning queue",
            "90-day scan history",
            "Multiple team members",
            "API analytics dashboard",
            "Slack integration"
        ]
    },
    "business": {
        "name": "Business",
        "price_monthly": 199,
        "scans_per_month": 500000,
        "rate_limit_per_hour": 2000,
        "cache_ttl": 86400,
        "features": [
            "All Pro features",
            "99.9% SLA",
            "1-year scan history",
            "White-label option",
            "Priority support (4h response)",
            "Custom integrations",
            "Dedicated account manager"
        ]
    }
}
```

### Billing Integration (Stripe)
```python
# app/services/billing.py
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_checkout_session(user_id: str, tier: str):
    """Create Stripe checkout session for tier upgrade"""
    
    price_ids = {
        "starter": settings.STRIPE_STARTER_PRICE_ID,
        "pro": settings.STRIPE_PRO_PRICE_ID,
        "business": settings.STRIPE_BUSINESS_PRICE_ID
    }
    
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': price_ids[tier],
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
        metadata={
            'user_id': user_id,
            'tier': tier
        }
    )
    
    return session.url
```

---

## Development Workflow

### Project Structure
```
secapi/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── docker.py
│   │   │   │   ├── iac.py
│   │   │   │   ├── secrets.py
│   │   │   │   └── scans.py
│   │   │   └── router.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings management
│   │   ├── security.py      # Auth helpers
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models.py
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── base.py          # Base scanner class
│   │   ├── trivy.py
│   │   ├── checkov.py
│   │   └── trufflehog.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scan.py          # Scan orchestration
│   │   ├── cache.py         # Redis caching
│   │   └── billing.py       # Stripe integration
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── scan.py          # Pydantic models
│   │   └── user.py
│   └── worker.py            # Celery worker
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_scanners/
│   └── test_services/
├── alembic/                 # Database migrations
│   ├── versions/
│   └── env.py
├── docs/
│   ├── self-hosting.md
│   ├── api-reference.md
│   └── architecture.md
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── README.md
├── LICENSE (MIT)
└── pyproject.toml
```

### Git Workflow
```bash
# Feature development
git checkout -b feature/iac-scanner
# ... make changes ...
git add .
git commit -m "feat(scanner): add Checkov IaC scanner"
git push origin feature/iac-scanner
# Create pull request

# Commit message format (Conventional Commits)
# feat: new feature
# fix: bug fix
# docs: documentation
# test: tests
# refactor: code refactoring
# chore: maintenance
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_scanners/test_trivy.py

# Run with verbose output
pytest -v

# Run security checks
bandit -r app/
safety check
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint
ruff check app/ tests/

# Type checking
mypy app/

# Pre-commit hook setup
pip install pre-commit
pre-commit install
```

---

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: secapi_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linters
      run: |
        black --check app/ tests/
        ruff check app/ tests/
        mypy app/
    
    - name: Run security checks
      run: |
        bandit -r app/
        safety check
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/secapi_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker image
      run: docker build -t secapi:latest .
    
    - name: Test Docker image
      run: |
        docker run --rm secapi:latest python -c "import app; print('OK')"
```

---

## Security Considerations

### Input Validation
```python
# Prevent malicious inputs
from pydantic import BaseModel, Field, validator

class DockerScanRequest(BaseModel):
    image: str = Field(..., max_length=500, pattern=r'^[\w\-\./:\@]+$')
    
    @validator('image')
    def validate_image_name(cls, v):
        # Prevent shell injection
        forbidden = [';', '&', '|', '`', '$', '(', ')']
        if any(char in v for char in forbidden):
            raise ValueError("Invalid image name")
        return v
```

### API Key Security
```python
# Hash API keys in database
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    key = f"sk_{''.join(secrets.token_urlsafe(32))}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash  # Store hash, give user key

def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key against stored hash"""
    computed_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)
```

### Rate Limiting
```python
# app/core/rate_limit.py
from fastapi import HTTPException, Request
from app.services.cache import redis_client

async def check_rate_limit(request: Request, user_id: str, tier: str):
    """Check if user exceeded rate limit"""
    
    limits = {
        "free": 10,      # per hour
        "starter": 100,
        "pro": 500,
        "business": 2000
    }
    
    limit = limits.get(tier, 10)
    key = f"ratelimit:{user_id}:{datetime.now().hour}"
    
    current = await redis_client.incr(key)
    
    if current == 1:
        await redis_client.expire(key, 3600)  # 1 hour
    
    if current > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {limit}/hour"
        )
```

---

## Monitoring & Observability

### Structured Logging
```python
# app/core/logging.py
import structlog

logger = structlog.get_logger()

# Usage in code
logger.info(
    "scan_completed",
    scan_id=scan_id,
    scan_type="docker",
    duration_ms=duration,
    vulnerabilities_found=vuln_count
)
```

### Prometheus Metrics
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram

scan_requests = Counter(
    'secapi_scan_requests_total',
    'Total scan requests',
    ['scan_type', 'status']
)

scan_duration = Histogram(
    'secapi_scan_duration_seconds',
    'Scan duration',
    ['scan_type']
)

# Usage
scan_requests.labels(scan_type='docker', status='success').inc()
scan_duration.labels(scan_type='docker').observe(2.3)
```

---

## Open Source Best Practices

### Community Engagement

1. **GitHub Discussions** - For Q&A and ideas
2. **Issue Templates** - Bug reports and feature requests
3. **Contributing Guide** - How to contribute
4. **Code of Conduct** - Community standards
5. **Changelog** - Track all changes
6. **Roadmap** - Public feature planning

### Release Process
```bash
# Version bump
bumpversion patch  # 0.1.0 -> 0.1.1

# Tag release
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin v0.1.1

# GitHub Actions auto-publishes Docker image
# and creates GitHub Release
```

---

## Instructions for Claude Code

When building SecAPI, follow these principles:

### Code Style
1. **Type hints everywhere** - All functions must have type annotations
2. **Async by default** - Use async/await for I/O operations
3. **Pydantic models** - All request/response objects use Pydantic
4. **Error handling** - Comprehensive try/except with proper error types
5. **Logging** - Structured logging for all operations
6. **Tests first** - Write tests before implementation (TDD)

### Architecture Decisions
1. **Keep scanners isolated** - Each scanner is a separate module
2. **Normalize early** - Convert scanner outputs immediately
3. **Cache aggressively** - Cache scan results for performance
4. **Queue heavy tasks** - Use Celery for long-running scans
5. **Database for audit** - Store all scans for compliance

### Open Source Focus
1. **Documentation first** - Every feature needs docs
2. **Self-hosting priority** - Ensure easy Docker deployment
3. **MIT License** - Permissive for maximum adoption
4. **Community-friendly** - Encourage contributions
5. **Transparent roadmap** - Public feature planning

### Security
1. **Input validation** - Sanitize all user inputs
2. **API key hashing** - Never store plaintext keys
3. **Rate limiting** - Prevent abuse
4. **Dependency scanning** - Run Safety/Bandit in CI
5. **Security.md** - Responsible disclosure policy

### Portfolio Emphasis
1. **Clean code** - Production-ready quality
2. **Comprehensive tests** - Show engineering discipline
3. **DevSecOps showcase** - Highlight security expertise
4. **Real-world usage** - Build for actual use cases
5. **Documentation** - Explain architectural decisions

### Implementation Order
When implementing features:
1. Start with API endpoint definition
2. Write Pydantic schemas
3. Implement service layer logic
4. Add scanner integration
5. Write comprehensive tests
6. Update documentation
7. Add usage examples

### Self-Hosting Instructions
Every feature must include:
1. **Docker Compose updates** - If services are needed
2. **Environment variables** - Document in .env.example
3. **Migration scripts** - Database changes
4. **Deployment guide** - Update docs/self-hosting.md
5. **Testing locally** - Verify works in Docker

### Managed Service Considerations
For paid tier features:
1. **Tier checks** - Validate user's tier before feature access
2. **Usage tracking** - Log for billing purposes
3. **Graceful degradation** - Free tier still functional
4. **Clear messaging** - Explain upgrade benefits
5. **Stripe integration** - Hook into billing system

The goal is to create a production-ready, well-documented open source project that demonstrates deep DevSecOps expertise while being genuinely useful to the developer community.

 ┌─────────────┬────────────┬─────────────────────────────────────────────────────────────────┐
  │    Phase    │  Duration  │                              Focus                              │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase1.md   │ Days 1-3   │ Foundation - Project setup, database, Docker, FastAPI core      │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase1-1.md │ Days 4-5   │ Trivy scanner - Docker image vulnerability scanning             │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase1-2.md │ Days 6-7   │ Checkov scanner - IaC security (Terraform, CloudFormation, K8s) │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase1-3.md │ Days 8-9   │ TruffleHog scanner - Secrets detection in Git/repos             │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase2.md   │ Days 10-11 │ Caching, rate limiting, performance metrics                     │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase3.md   │ Days 12-13 │ Testing (80%+ coverage), API docs, self-hosting guides          │
  ├─────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
  │ phase4.md   │ Days 14-15 │ CI/CD, Docker publishing, production deployment                 │
  └─────────────┴────────────┴───────────────────────────────────────────────────