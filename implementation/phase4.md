# Phase 4: CI/CD & Deployment (Days 14-15)

**Goal**: Set up CI/CD pipelines, Docker publishing, and production deployment configuration.

## Overview

This phase automates the build, test, and deployment process. You'll create GitHub Actions workflows, set up automated Docker image publishing, configure production deployment, and prepare for launch.

## Tasks Checklist

### 4.1 GitHub Actions CI/CD (Day 14 - Morning)

- [ ] Create CI workflow for testing
- [ ] Add automated testing on PRs
- [ ] Add code quality checks
- [ ] Add security scanning steps
- [ ] Create Docker build workflow
- [ ] Add release workflow
- [ ] Set up deployment workflow

**Files to Create:**
```
.github/
└── workflows/
    ├── ci.yml           # Continuous Integration
    ├── docker.yml       # Docker Image Build
    ├── release.yml      # Release & Publish
    └── deploy.yml       # Deployment
```

**CI Workflow:**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

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
```

**Deliverables:**
- Working CI pipeline
- Automated testing on push/PR
- Code quality checks
- Security scanning
- Coverage reporting

### 4.2 Docker Image Publishing (Day 14 - Afternoon)

- [ ] Create Docker build workflow
- [ ] Set up multi-arch builds (amd64, arm64)
- [ ] Configure Docker Hub publishing
- [ ] Add image tagging strategy
- [ ] Set up GitHub Container Registry
- [ ] Add vulnerability scanning to builds

**Docker Workflow:**
```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            yourusername/secapi
            ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy on image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.meta.outputs.tags }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

**Deliverables:**
- Automated Docker builds
- Multi-arch support (amd64, arm64)
- Docker Hub publishing
- GHCR publishing
- Vulnerability scanning

### 4.3 Production Docker Configuration (Day 15 - Morning)

- [ ] Create production Dockerfile
- [ ] Create production docker-compose
- [ ] Add health checks
- [ ] Configure resource limits
- [ ] Add graceful shutdown
- [ ] Create nginx configuration

**Files to Create:**
```
Dockerfile.prod
docker-compose.prod.yml
nginx/
└── secapi.conf
```

**Production Dockerfile:**
```dockerfile
FROM python:3.11-slim as base

# Install security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | \
    sh -s -- -b /usr/local/bin

# Install Checkov & TruffleHog
RUN pip install --no-cache-dir checkov trufflehog

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 secapi && \
    chown -R secapi:secapi /app

USER secapi

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Production Compose:**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    command: celery -A app.worker worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    volumes:
      - trivy_cache:/home/secapi/.cache/trivy
      - /var/run/docker.sock:/var/run/docker.sock
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/secapi.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
  trivy_cache:
```

**Deliverables:**
- Production-optimized Dockerfile
- Production docker-compose
- Health checks
- Resource limits
- Nginx configuration

### 4.4 Deployment Automation (Day 15 - Afternoon)

- [ ] Create deployment script
- [ ] Add database migration automation
- [ ] Set up backup scripts
- [ ] Create monitoring setup
- [ ] Add log aggregation
- [ ] Write deployment documentation

**Files to Create:**
```
scripts/
├── deploy.sh
├── backup.sh
└── migrate.sh

docs/
└── deployment.md
```

**Deploy Script:**
```bash
#!/bin/bash
set -e

echo "🚀 Deploying SecAPI..."

# Pull latest changes
git pull origin main

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Run health check
if curl -f http://localhost:8000/health; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed!"
    exit 1
fi
```

**Deliverables:**
- Automated deployment script
- Database migration automation
- Backup scripts
- Monitoring configuration
- Deployment documentation

## Acceptance Criteria

Phase 4 is complete when:

1. ✅ CI pipeline runs on every push
2. ✅ All tests pass in CI
3. ✅ Docker images build and publish automatically
4. ✅ Multi-arch images are available
5. ✅ Production docker-compose works
6. ✅ Health checks pass
7. ✅ Deployment script works end-to-end
8. ✅ Documentation is complete

## Commands for Phase 4

```bash
# Test CI locally
act -j test  # Using nektos/act

# Build Docker image
docker buildx build --platform linux/amd64,linux/arm64 -t secapi:test .

# Test production compose
docker-compose -f docker-compose.prod.yml config
docker-compose -f docker-compose.prod.yml up -d

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Check health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database backup created
- [ ] DNS configured
- [ ] Firewall rules set

### Deployment
- [ ] Pull latest code
- [ ] Run database migrations
- [ ] Pull Docker images
- [ ] Restart services
- [ ] Verify health checks

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify API endpoints
- [ ] Check Celery workers
- [ ] Monitor metrics
- [ ] Test core functionality

## Production Considerations

### Security
- Use secrets manager for sensitive data
- Enable HTTPS with valid certificates
- Configure firewall rules
- Regular security updates
- Monitor for vulnerabilities

### Monitoring
- Application metrics (Prometheus)
- Log aggregation (Loki/ELK)
- Error tracking (Sentry)
- Uptime monitoring
- Performance monitoring

### Backups
- Database backups (daily)
- Redis backups (if needed)
- Configuration backups
- Test restore procedures

## Notes

- Test deployment scripts in staging first
- Have rollback plan ready
- Monitor deployment closely
- Document any issues
- Keep deployment logs

## Next Phase

After completing Phase 4, SecAPI is ready for **Launch!** Proceed to marketing, community engagement, and continuous improvement.
