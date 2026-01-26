# Phase 1-3: TruffleHog Scanner Integration (Days 8-9)

**Goal**: Implement TruffleHog scanner for secrets detection in Git repositories and code.

## Overview

This phase adds secrets detection using TruffleHog. This scanner searches for exposed credentials, API keys, and other sensitive information in Git repositories and code content. Scans are asynchronous due to potential repository size.

## Tasks Checklist

### 1.1 TruffleHog Scanner Implementation (Day 8 - Morning)

- [ ] Ensure TruffleHog is installed in Docker image
- [ ] Implement `TruffleHogScanner` class
- [ ] Add support for Git repository scanning
- [ ] Add support for inline code/content scanning
- [ ] Parse TruffleHog JSON output
- [ ] Normalize to unified format
- [ ] Handle Git clone/cleanup

**Files to Create:**
```
app/scanners/
└── trufflehog.py     # TruffleHogScanner implementation
```

**TruffleHogScanner Methods:**
```python
class TruffleHogScanner(BaseScanner):
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TruffleHog scan for secrets"""
        # 1. Validate input (type: git or content)
        # 2. If git: clone repo to temp dir
        # 3. Build TruffleHog command
        # 4. Execute subprocess
        # 5. Parse JSON output
        # 6. Normalize to unified format
        # 7. Cleanup temp dirs

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate secrets scan input"""
        # Check source type (git or content)
        # Validate Git URL format
        # Check content is not empty

    def _clone_repo(self, url: str, branch: str = "main") -> Path:
        """Clone Git repo to temporary directory"""
        # Clone to temp location
        # Return path

    def _normalize_output(self, raw: List[Dict]) -> Dict[str, Any]:
        """Convert TruffleHog output to unified format"""
        # Extract findings with metadata
        # Categorize by secret type
        # Redact actual secret values
```

**TruffleHog Commands:**
```bash
# Git repository
trufflehog git https://github.com/user/repo --json

# Specific branch
trufflehog git https://github.com/user/repo --branch develop --json

# Inline content (via stdin)
echo "code here" | trufflehog stdin --json
```

**Deliverables:**
- Working TruffleHog scanner for Git repos
- Working TruffleHog scanner for inline content
- Git clone/cleanup handling
- Output normalization with redaction

### 1.2 Secrets Scan Schemas (Day 8 - Afternoon)

- [ ] Create secrets scan request schemas
- [ ] Create secrets-specific response schemas
- [ ] Add Git URL validation
- [ ] Add branch/commit support
- [ ] Add secret metadata schemas

**Files to Create:**
```
app/schemas/
└── secrets.py        # Secrets-specific schemas
```

**Request Schema:**
```python
class SecretsScanRequest(BaseModel):
    source: Literal["git", "content"]
    repository: Optional[str] = None  # For git source
    branch: Optional[str] = "main"
    commit: Optional[str] = None  # Specific commit hash
    content: Optional[str] = None  # For content source
    max_depth: Optional[int] = 5  # Git history depth
```

**Response Schema:**
```python
class SecretsScanResponse(BaseModel):
    scan_id: str
    status: Literal["completed", "failed", "scanning"]
    scan_type: Literal["secrets"]
    findings: List[SecretFinding]
    summary: Dict[str, int]  # By secret type
    scanned_files: int
    scanned_commits: int
```

**Finding Schema:**
```python
class SecretFinding(BaseModel):
    id: str  # Finding ID
    severity: Literal["CRITICAL", "HIGH"]  # All secrets are critical/high
    secret_type: str  # e.g., "AWS Access Key", "GitHub Token"
    title: str
    description: str
    file: str
    line: int
    commit: Optional[str] = None  # Commit hash where found
    author: Optional[str] = None  # Commit author
    date: Optional[str] = None  # Commit date
    redacted_value: str  # Show partial secret only
    detector: str  # Which detector found it
```

**Deliverables:**
- Pydantic schemas for secrets scanning
- Git URL validation
- Secret type categorization
- Value redaction for security

### 1.3 Secrets API Endpoints (Day 9 - Morning)

- [ ] Implement `POST /api/v1/scan/secrets` endpoint
- [ ] Add async task execution (Celery)
- [ ] Add Git repository scanning
- [ ] Add inline content scanning
- [ ] Implement result caching
- [ ] Add rate limiting (expensive operation)
- [ ] Write API tests

**Files to Create:**
```
app/api/v1/endpoints/
└── secrets.py        # Secrets scan endpoints
```

**Endpoints:**
```http
# Queue secrets scan (async - takes time for repos)
POST /api/v1/scan/secrets
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "source": "git",
  "repository": "https://github.com/user/repo",
  "branch": "main",
  "max_depth": 10
}

Response 202:
{
  "scan_id": "770e8400-...",
  "status": "queued",
  "estimated_time": "30s",
  "check_status_url": "/api/v1/scans/770e8400-..."
}

# Inline content (faster)
{
  "source": "content",
  "content": "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nexport AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```

**Deliverables:**
- Working secrets scan endpoint
- Async Git repository scanning
- Synchronous inline content scanning
- Result caching with content hash
- Enhanced rate limiting

### 1.4 Secrets Testing & Security (Day 9 - Afternoon)

- [ ] Write tests for Git scanning
- [ ] Write tests for content scanning
- [ ] Test secret redaction
- [ ] Test error scenarios (invalid repos, private repos)
- [ ] Add security measures (no secret logging)
- [ ] Create usage examples
- [ ] Update documentation

**Security Measures:**
```python
# NEVER log actual secrets
logger.info("secret_found", secret_type="AWS Key", file="config.py")

# Always redact in output
redacted = f"{secret[:4]}...{secret[-4:]}"

# Cleanup temp files securely
shred.rmtree(temp_dir)  # Secure deletion
```

**Test Cases:**
- Public GitHub repo scan
- GitLab/Bitbucket repo scan
- Specific branch scanning
- Specific commit scanning
- Inline content with secrets
- Content without secrets
- Invalid repository URL
- Private repository (should fail gracefully)
- Large repository handling

**Deliverables:**
- Comprehensive test suite
- Security measures for secret handling
- Usage examples
- Security documentation

## Acceptance Criteria

Phase 1-3 is complete when:

1. ✅ `POST /api/v1/scan/secrets` scans Git repositories
2. ✅ `POST /api/v1/scan/secrets` scans inline content
3. ✅ Secrets are redacted in results (never shown)
4. ✅ Git repos are cloned and cleaned up properly
5. ✅ Results are normalized to unified format
6. ✅ Rate limiting is stricter for expensive Git scans
7. ✅ All tests pass with 80%+ coverage
8. ✅ No secrets are logged anywhere

## Commands for Phase 1-3

```bash
# Test TruffleHog locally
trufflehog git https://github.com/test/repo --json
echo "const key = 'sk_test_123'" | trufflehog stdin --json

# Run tests
pytest tests/test_scanners/test_trufflehog.py -v
pytest tests/test_api/test_secrets.py -v

# Test API - Git scan
curl -X POST http://localhost:8000/api/v1/scan/secrets \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "git",
    "repository": "https://github.com/trufflesecurity/test_keys"
  }'

# Test API - Content scan
curl -X POST http://localhost:8000/api/v1/scan/secrets \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "content",
    "content": "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
  }'

# Monitor Celery
docker-compose logs -f worker
```

## API Examples

```bash
# Scan GitHub repository
curl -X POST http://localhost:8000/api/v1/scan/secrets \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "git",
    "repository": "https://github.com/username/repo",
    "branch": "main",
    "max_depth": 5
  }'

# Scan specific commit
curl -X POST http://localhost:8000/api/v1/scan/secrets \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "git",
    "repository": "https://github.com/username/repo",
    "commit": "abc123def456"
  }'

# Scan inline code
curl -X POST http://localhost:8000/api/v1/scan/secrets \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "content",
    "content": "const dbPassword = \"SuperSecret123\";\nconst apiKey = \"sk_live_abc123\";"
  }'

# Get results
curl http://localhost:8000/api/v1/scans/{scan_id} \
  -H "Authorization: Bearer $API_KEY"
```

## Notes

- Git scans MUST be async (can take minutes)
- Content scans can be sync (fast)
- Always redact secrets - never return full values
- Clean up temp Git repos securely
- Rate limit Git scans more aggressively
- Support GitHub, GitLab, Bitbucket URLs
- Private repos need auth (optional enhancement)
- Never log actual secret values

## Next Phase

After completing Phase 1-3, proceed to **Phase 2: Caching, Performance & Rate Limiting** to optimize the platform.
