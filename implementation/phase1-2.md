# Phase 1-2: Checkov Scanner Integration (Days 6-7)

**Goal**: Implement Checkov scanner for Infrastructure-as-Code (IaC) security scanning.

## Overview

This phase adds IaC security scanning using Checkov. Unlike Docker scans which run asynchronously, IaC scans are typically faster and can be run synchronously. You'll implement the Checkov scanner, create API endpoints, and handle Terraform/CloudFormation/Kubernetes formats.

## Tasks Checklist

### 1.1 Checkov Scanner Implementation (Day 6 - Morning)

- [ ] Ensure Checkov is installed in Docker image
- [ ] Implement `CheckovScanner` class
- [ ] Add support for Terraform scanning
- [ ] Add support for CloudFormation scanning
- [ ] Add support for Kubernetes scanning
- [ ] Parse Checkov JSON output
- [ ] Normalize to unified format

**Files to Create:**
```
app/scanners/
└── checkov.py         # CheckovScanner implementation
```

**CheckovScanner Methods:**
```python
class CheckovScanner(BaseScanner):
    async def scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Checkov scan on IaC content"""
        # 1. Validate input (type, content)
        # 2. Create temp file with content
        # 3. Build Checkov command
        # 4. Execute subprocess
        # 5. Parse JSON output
        # 6. Normalize to unified format
        # 7. Cleanup temp files

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate IaC type and content"""
        # Check type is supported (terraform, cloudformation, kubernetes)
        # Check content is not empty
        # Basic syntax validation

    def _normalize_output(self, raw: Dict, iac_type: str) -> Dict[str, Any]:
        """Convert Checkov output to unified format"""
        # Map Checkov checks to findings
        # Extract severity from check_id
        # Format resource locations
```

**Checkov Commands:**
```bash
# Terraform
checkov -f tempfile.tf --framework terraform --output json --quiet

# CloudFormation
checkov -f tempfile.yaml --framework cloudformation --output json --quiet

# Kubernetes
checkov -f tempfile.yaml --framework kubernetes --output json --quiet
```

**Deliverables:**
- Working Checkov scanner for Terraform
- Working Checkov scanner for CloudFormation
- Working Checkov scanner for Kubernetes
- Input validation for each type
- Output normalization

### 1.2 IaC Scan Schemas (Day 6 - Afternoon)

- [ ] Create IaC scan request schemas
- [ ] Create IaC-specific response schemas
- [ ] Add support for custom policies
- [ ] Add support for file uploads
- [ ] Add schema validation

**Files to Create:**
```
app/schemas/
└── iac.py            # IaC-specific schemas
```

**Request Schema:**
```python
class IaCScanRequest(BaseModel):
    type: Literal["terraform", "cloudformation", "kubernetes"]
    content: str = Field(..., min_length=1, max_length=100000)
    policies: Optional[List[str]] = None  # Custom policy IDs
    source: Optional[Literal["raw", "file"]] = "raw"
```

**Response Schema:**
```python
class IaCScanResponse(BaseModel):
    scan_id: str
    status: Literal["completed", "failed"]
    scan_type: Literal["iac"]
    findings: List[IaCFinding]
    summary: Dict[str, int]
    scanned_resources: int
    passed_checks: int
    failed_checks: int
```

**Deliverables:**
- Pydantic schemas for IaC scanning
- Support for all three IaC types
- Custom policy support
- File upload support

### 1.3 IaC API Endpoints (Day 7 - Morning)

- [ ] Implement `POST /api/v1/scan/iac` endpoint
- [ ] Add support for file uploads
- [ ] Add policy checking
- [ ] Implement result caching
- [ ] Add error handling for invalid IaC
- [ ] Write API tests

**Files to Create:**
```
app/api/v1/endpoints/
└── iac.py            # IaC scan endpoints
```

**Endpoints:**
```http
# Scan IaC (synchronous - faster than Docker scans)
POST /api/v1/scan/iac
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "type": "terraform",
  "content": "resource \"aws_s3_bucket\" \"example\" {\n  # ...\n}",
  "policies": ["CKV_AWS_18", "CKV_AWS_20"]
}

Response 200:
{
  "scan_id": "660e8400-...",
  "status": "completed",
  "scan_type": "iac",
  "iac_type": "terraform",
  "created_at": "2025-01-25T10:30:00Z",
  "completed_at": "2025-01-25T10:30:05Z",
  "findings": [
    {
      "id": "CKV_AWS_18",
      "severity": "HIGH",
      "title": "S3 Bucket should have access logging enabled",
      "description": "Ensure S3 buckets have access logging...",
      "resource": "aws_s3_bucket.example",
      "file": "main.tf",
      "line": 5,
      "category": "LOGGING"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 5
  },
  "scanned_resources": 10,
  "passed_checks": 15,
  "failed_checks": 9
}

# File upload version
POST /api/v1/scan/iac/file
Authorization: Bearer <api_key>
Content-Type: multipart/form-data

type: terraform
file: main.tf
```

**Deliverables:**
- Working IaC scan endpoint
- File upload support
- Custom policy filtering
- Result caching
- Error handling for invalid IaC

### 1.4 IaC Testing & Examples (Day 7 - Afternoon)

- [ ] Write tests for all IaC types
- [ ] Create test IaC files
- [ ] Test error scenarios
- [ ] Create usage examples
- [ ] Update documentation
- [ ] Add performance benchmarks

**Test Cases:**
- Valid Terraform scan
- Valid CloudFormation scan
- Valid Kubernetes scan
- Invalid IaC syntax
- Empty content
- Oversized content
- Custom policy filtering
- File upload

**Example IaC Files for Testing:**
```terraform
# tests/fixtures/iac/vulnerable.tf
resource "aws_s3_bucket" "example" {
  bucket = "my-test-bucket"
  acl    = "public-read"  # Finding: public bucket

  versioning {
    enabled = false  # Finding: no versioning
  }
}
```

**Deliverables:**
- Comprehensive test suite
- Test fixtures for each IaC type
- Usage examples in README
- API documentation

## Acceptance Criteria

Phase 1-2 is complete when:

1. ✅ `POST /api/v1/scan/iac` scans all three IaC types
2. ✅ Results are normalized to unified format
3. ✅ File uploads work correctly
4. ✅ Custom policy filtering works
5. ✅ Invalid IaC returns helpful error messages
6. ✅ All tests pass with 80%+ coverage
7. ✅ Scans complete in <10 seconds (synchronous)

## Commands for Phase 1-2

```bash
# Test Checkov locally
checkov -f tests/fixtures/iac/vulnerable.tf --framework terraform --output json

# Run tests
pytest tests/test_scanners/test_checkov.py -v
pytest tests/test_api/test_iac.py -v

# Test API
curl -X POST http://localhost:8000/api/v1/scan/iac \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "terraform",
    "content": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"test\"\n}"
  }'

# Test file upload
curl -X POST http://localhost:8000/api/v1/scan/iac/file \
  -H "Authorization: Bearer <api_key>" \
  -F "type=terraform" \
  -F "file=@main.tf"
```

## API Examples

```bash
# Terraform scan
curl -X POST http://localhost:8000/api/v1/scan/iac \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "terraform",
    "content": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n  acl = \"public-read\"\n}"
  }'

# CloudFormation scan
curl -X POST http://localhost:8000/api/v1/scan/iac \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "cloudformation",
    "content": "AWSTemplateFormatVersion: \"2010-09-09\"\nResources:\n  MyBucket:\n    Type: AWS::S3::Bucket\n    Properties:\n      PublicAccessBlockConfiguration: {...}"
  }'

# Kubernetes scan
curl -X POST http://localhost:8000/api/v1/scan/iac \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "kubernetes",
    "content": "apiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - name: nginx\n    image: nginx:latest\n    securityContext:\n      privileged: true"
  }'
```

## Notes

- IaC scans are faster than Docker scans - run synchronously
- Still use Celery for very large IaC files (optional)
- Cache based on content hash
- Support both inline content and file uploads
- Provide helpful error messages for syntax errors
- Consider supporting GitHub URLs for IaC files

## Next Phase

After completing Phase 1-2, proceed to **Phase 1-3: TruffleHog Scanner Integration** to add secrets detection capabilities.
