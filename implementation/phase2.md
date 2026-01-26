# Phase 2: Caching, Performance & Rate Limiting (Days 10-11)

**Goal**: Implement intelligent caching, performance optimizations, and tiered rate limiting.

## Overview

This phase focuses on making SecAPI production-ready with intelligent caching, performance monitoring, and rate limiting based on user tiers. You'll implement Redis caching strategies, performance metrics, and tier-based access control.

## Tasks Checklist

### 2.1 Redis Caching Layer (Day 10 - Morning)

- [ ] Create cache service module
- [ ] Implement scan result caching
- [ ] Add cache invalidation logic
- [ ] Add cache warming strategies
- [ ] Implement cache statistics
- [ ] Add cache control headers

**Files to Create:**
```
app/services/
└── cache.py          # Redis caching service

app/core/
└── cache.py          # Cache decorators and helpers
```

**Cache Service:**
```python
class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_scan_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached scan result"""

    async def set_scan_result(
        self,
        cache_key: str,
        result: Dict,
        ttl: int = 86400  # 24 hours default
    ):
        """Cache scan result with TTL"""

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""

    async def get_cache_stats(self) -> Dict:
        """Get cache hit/miss statistics"""
```

**Cache Strategies:**
```python
# Scan result cache key
cache_key = f"scan:{scan_type}:{hash(input_params)}"

# TTL by tier
CACHE_TTL = {
    "free": 3600,      # 1 hour
    "starter": 86400,  # 24 hours
    "pro": 86400,
    "business": 604800 # 7 days
}
```

**Deliverables:**
- Working Redis cache service
- Scan result caching
- Tier-based TTL
- Cache statistics
- Cache invalidation

### 2.2 Rate Limiting by Tier (Day 10 - Afternoon)

- [ ] Implement tier-based rate limiting
- [ ] Add rate limit checking middleware
- [ ] Create rate limit exceeded exceptions
- [ ] Add rate limit headers to responses
- [ ] Implement sliding window algorithm
- [ ] Add rate limit reset notifications

**Files to Create:**
```
app/core/
└── rate_limit.py     # Rate limiting service
```

**Rate Limiting:**
```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        user_id: str,
        tier: str,
        endpoint: str
    ) -> RateLimitResult:
        """
        Check if user exceeded rate limit

        Returns:
            RateLimitResult with:
            - allowed: bool
            - remaining: int
            - reset_at: datetime
            - limit: int
        """

    async def record_request(
        self,
        user_id: str,
        endpoint: str
    ):
        """Record API request for rate limiting"""
```

**Rate Limits by Tier:**
```python
RATE_LIMITS = {
    "free": {
        "scans_per_hour": 10,
        "scans_per_month": 100,
        "api_requests_per_minute": 20
    },
    "starter": {
        "scans_per_hour": 100,
        "scans_per_month": 5000,
        "api_requests_per_minute": 100
    },
    "pro": {
        "scans_per_hour": 500,
        "scans_per_month": 50000,
        "api_requests_per_minute": 500
    },
    "business": {
        "scans_per_hour": 2000,
        "scans_per_month": 500000,
        "api_requests_per_minute": 2000
    }
}
```

**Deliverables:**
- Tier-based rate limiting
- Sliding window algorithm
- Rate limit headers in responses
- Graceful error messages
- Rate limit reset notifications

### 2.3 Performance Metrics (Day 11 - Morning)

- [ ] Set up Prometheus metrics
- [ ] Add scan request counter
- [ ] Add scan duration histogram
- [ ] Add cache hit/miss tracking
- [ ] Add error rate tracking
- [ ] Create `/metrics` endpoint
- [ ] Add custom performance dashboards

**Files to Create:**
```
app/core/
└── metrics.py        # Prometheus metrics
```

**Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Scan metrics
scan_requests = Counter(
    'secapi_scan_requests_total',
    'Total scan requests',
    ['scan_type', 'status', 'tier']
)

scan_duration = Histogram(
    'secapi_scan_duration_seconds',
    'Scan duration in seconds',
    ['scan_type']
)

# Cache metrics
cache_hits = Counter(
    'secapi_cache_hits_total',
    'Total cache hits',
    ['scan_type']
)

cache_misses = Counter(
    'secapi_cache_misses_total',
    'Total cache misses',
    ['scan_type']
)

# Rate limit metrics
rate_limit_exceeded = Counter(
    'secapi_rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['tier', 'endpoint']
)
```

**Deliverables:**
- Prometheus metrics integration
- Scan performance tracking
- Cache performance tracking
- Rate limit tracking
- `/metrics` endpoint

### 2.4 Database Optimization (Day 11 - Afternoon)

- [ ] Add database indexes
- [ ] Optimize slow queries
- [ ] Add connection pooling configuration
- [ ] Implement query result caching
- [ ] Add database health monitoring
- [ ] Create database migration for indexes

**Database Indexes:**
```sql
-- Optimize scan lookups
CREATE INDEX idx_scans_user_created ON scans(user_id, created_at DESC);
CREATE INDEX idx_scans_status_type ON scans(status, scan_type);

-- Optimize rate limit queries
CREATE INDEX idx_rate_limits_user_period ON rate_limits(user_id, period_start);

-- Optimize usage analytics
CREATE INDEX idx_api_usage_user_timestamp ON api_usage(user_id, timestamp DESC);

-- Optimize cache lookups
CREATE INDEX idx_scans_input_hash ON scans(md5(input_data::text));
```

**Query Optimization:**
```python
# Add select_related/prefetch for common queries
query = (
    select(Scan)
    .where(Scan.user_id == user_id)
    .order_by(Scan.created_at.desc())
    .limit(20)
)

# Use EXPLAIN ANALYZE to verify
```

**Deliverables:**
- Database indexes for common queries
- Optimized queries
- Connection pooling configured
- Query result caching
- Database performance monitoring

### 2.5 Performance Testing & Tuning (Day 11 - Late Afternoon)

- [ ] Create load tests with Locust
- [ ] Run performance benchmarks
- [ ] Identify bottlenecks
- [ ] Tune database connection pool
- [ ] Tune Redis connection pool
- [ ] Add performance baselines
- [ ] Document performance characteristics

**Files to Create:**
```
tests/load/
└── locustfile.py     # Load testing scenarios
```

**Load Test:**
```python
from locust import HttpUser, task, between

class SecAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def docker_scan(self):
        self.client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

    @task(3)
    def get_scan_results(self):
        self.client.get(
            f"/api/v1/scans/{SCAN_ID}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
```

**Deliverables:**
- Load test suite
- Performance benchmarks
- Tuned connection pools
- Performance documentation
- Baseline metrics

## Acceptance Criteria

Phase 2 is complete when:

1. ✅ Scan results are cached in Redis
2. ✅ Cache hits return <100ms
3. ✅ Rate limiting works per tier
4. ✅ Rate limit headers are present
5. ✅ Prometheus metrics are available
6. ✅ Database queries are optimized
7. ✅ Load tests pass (100 concurrent users)
8. ✅ `/metrics` endpoint returns metrics

## Commands for Phase 2

```bash
# Check cache stats
redis-cli
> KEYS scan:*
> TTL scan:docker:abc123
> GET scan:docker:abc123

# Test rate limiting
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/scan/docker \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"image": "nginx:latest"}'
done
# Should hit rate limit

# View metrics
curl http://localhost:8000/metrics

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Database query analysis
docker-compose exec db psql -U postgres -d secapi
EXPLAIN ANALYZE SELECT * FROM scans WHERE user_id = '...' ORDER BY created_at DESC LIMIT 20;

# Check cache performance
redis-cli INFO stats
```

## API Examples

```bash
# First request - cache miss
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:1.24"}'

# Response headers:
# X-Cache-Status: MISS
# X-RateLimit-Remaining: 9
# X-RateLimit-Reset: 1706188800

# Second request - cache hit
curl -X POST http://localhost:8000/api/v1/scan/docker \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:1.24"}'

# Response headers:
# X-Cache-Status: HIT
# X-RateLimit-Remaining: 9

# View metrics
curl http://localhost:8000/metrics | grep secapi
```

## Performance Targets

- **Cache hit response**: <100ms
- **Cache miss response**: <2s (synchronous), <5s (async queued)
- **Database query**: <50ms (indexed)
- **Rate limit check**: <10ms
- **Concurrent users**: 100+
- **Requests/second**: 50+ (per instance)

## Notes

- Cache keys should include input parameters hash
- Different TTL per tier
- Rate limits should be sliding window
- Monitor cache hit rate (target: 60%+)
- Add monitoring alerts for cache miss rate
- Document performance characteristics

## Next Phase

After completing Phase 2, proceed to **Phase 3: Testing & Documentation** to prepare for production launch.
