# SecAPI

Open-source security scanning API platform that wraps Trivy, Checkov, and TruffleHog into a unified REST API.

## Quick Start

### Option 1: Use the run script (Easiest)

```bash
./run.sh
```

This will:
- Create a virtual environment if needed
- Install dependencies
- Start the server at http://localhost:8000

### Option 2: Docker Compose (Full Stack with Database)

```bash
docker-compose up -d
```

Includes PostgreSQL, Redis, and the API.

### Option 3: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

## Running Locally

**Fastest way (no install needed for basic testing):**
```bash
./run.sh
```

**With Docker (includes database):**
```bash
docker-compose up -d
```

## API Endpoints

Once running:
- `GET http://localhost:8000/` - API info
- `GET http://localhost:8000/health` - Health check
- `GET http://localhost:8000/docs` - Interactive API docs (Swagger UI)
- `GET http://localhost:8000/redoc` - ReDoc documentation

## Quick Test

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

## Project Structure

```
secapi/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Config, security, logging
│   ├── db/              # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   └── main.py          # FastAPI app factory
├── tests/               # Test suite
├── alembic/             # Database migrations
├── docker-compose.yml   # Dev infrastructure
└── run.sh              # Quick start script
```



## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Cache/Queue**: Redis
- **Security Scanners**: Trivy, Checkov, TruffleHog (coming in Phase 2)
- **Testing**: pytest
- **Code Quality**: black, ruff, mypy
- **Deployment**: Docker, Docker Compose

## Current Status

**Phase 1 Complete**: Foundation & Core Infrastructure
- Project structure
- FastAPI application
- Database models
- Docker setup
- API key authentication

**Next**: Trivy scanner integration (Phase 1-1)

## License

MIT License
