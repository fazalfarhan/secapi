# SecAPI

Open-source security scanning API platform that wraps Trivy, Checkov, and TruffleHog into a unified REST API.

## Features

- 🚀 **Unified API** - Single interface for multiple security scanners
- 🔒 **API Key Authentication** - Secure API key-based auth
- 📊 **Async Processing** - Fast async/await patterns
- 🐳 **Docker Ready** - Self-hosted with Docker Compose
- 📈 **Rate Limiting** - Built-in rate limiting per tier
- 🔄 **Queue System** - Celery for background jobs

## Quick Start

### Docker Compose (Recommended)

```bash
cp .env.example .env
docker-compose up -d
```

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Database
alembic upgrade head

# Run
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API docs

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Cache/Queue**: Redis, Celery
- **Security**: Trivy, Checkov, TruffleHog
- **Deployment**: Docker, Docker Compose

## License

MIT License - see [LICENSE](LICENSE) for details.
