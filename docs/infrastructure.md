# CampusOS Production Infrastructure Architecture

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. System Topology & Network Architecture

CampusOS is structured as a cloud-neutral, modular SaaS application:

```text
                          Internet
                             │
                             ▼
                     Cloudflare CDN / WAF
                             │
                             ▼
                     Nginx Reverse Proxy
                      (TLS Termination)
                      ┌──────┴──────┐
                      │             │
                      ▼             ▼
             Next.js Frontend    FastAPI Backend
              (app.campus.edu)   (api.campus.edu)
                      │                 │
                      │           ┌─────┴─────┐
                      │           │           │
                      │           ▼           ▼
                      │      PostgreSQL     Redis
                      │      (Primary)      (Cache/Lock)
                      │           │           │
                      │           │           ▼
                      │           │       Worker & Scheduler
                      │           ▼
                      │      Object Storage
                      │      (S3/Documents)
                      ▼
                 Web Users
```

---

## 2. PostgreSQL Production Configuration

CampusOS requires PostgreSQL 16+ with high-performance connection pooling:

### Application-Side Connection Pool (SQLAlchemy + AsyncPG)
- **`DB_POOL_SIZE`**: `25` persistent connections per API replica.
- **`DB_MAX_OVERFLOW`**: `15` burst connections per replica during load spikes.
- **`DB_POOL_TIMEOUT`**: `30` seconds maximum wait time before timeout exception.
- **`DB_POOL_RECYCLE`**: `1800` seconds (30 minutes) to eliminate stale socket connections.

### Database Server Parameters
```ini
# Recommended PostgreSQL Configuration
shared_buffers = 512MB
effective_cache_size = 1536MB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
max_connections = 150
statement_timeout = 30000ms        # 30 second bound to prevent DoS
idle_in_transaction_session_timeout = 60000ms
```

---

## 3. Redis Production Configuration

Redis provides low-latency caching, tenant-isolated rate limiting, and distributed locking:

- **Authentication:** `requirepass <high-entropy-secret>` enabled.
- **Eviction Policy:** `maxmemory-policy allkeys-lru` (safely evicts oldest cached keys when memory limit reached).
- **Memory Limit:** `512MB` for staging/small colleges; `2GB` for large universities.
- **Data Categories:**
  - **Cache:** `tenant:{tenant_id}:{namespace}:{key}` (TTL 300s).
  - **Locks:** `campusos:lock:{job_name}` (TTL 60s–300s).
  - **Rate Limiting:** `rl:{tenant_id}:{user_id}:{category}` (sliding window timestamps).

---

## 4. Background Workers & Distributed Scheduler

### Asynchronous Worker (`apps/api/app/worker.py`)
- Executes CPU-bound and asynchronous tasks:
  - Document thumbnail generation & virus scanning
  - PDF transcript & fee receipt generation
  - Email & SMS notification dispatch
  - Analytics rollups and aggregation
- Guarantees:
  - Every job retains explicit `tenant_id`, `job_id`, and `correlation_id`.
  - Independent fault domains: an error in Tenant A cannot affect Tenant B.

### Distributed Scheduler (`apps/api/app/scheduler.py`)
- Executes recurring institutional maintenance tasks:
  - Document expiration checks
  - Fee overdue fee assessment
  - Attendance low-threshold alerts
  - Notification batch processing
- Guarantees:
  - Uses `distributed_lock` in Redis with safe token ownership verification to prevent duplicate executions across multiple worker replicas.

---

## 5. Domain & DNS Architecture

| Subdomain | Target | Purpose | TLS Source |
| :--- | :--- | :--- | :--- |
| `app.campus.edu` | Web Replicas (Port 3000) | Primary User Interface | Cloudflare / Let's Encrypt |
| `api.campus.edu` | API Replicas (Port 8000) | REST API & WebSocket | Cloudflare / Let's Encrypt |
| `staging.campus.edu` | Staging Web | Staging UI | Cloudflare / Let's Encrypt |
| `staging-api.campus.edu`| Staging API | Staging API | Cloudflare / Let's Encrypt |

---

## 6. Sizing & Resource Guidance

### Recommended Starting Quotas (Per 5,000 Students)
- **Web Replicas (Next.js):** 2 instances × (1.0 CPU, 1024 MB RAM).
- **API Replicas (FastAPI):** 2 instances × (1.5 CPU, 1536 MB RAM, 4 Uvicorn workers).
- **Worker Replicas:** 1 instance × (1.0 CPU, 1024 MB RAM).
- **Scheduler Replicas:** 1 instance × (0.5 CPU, 512 MB RAM).
- **PostgreSQL:** 2 vCPU, 4096 MB RAM, 100 GB SSD storage.
- **Redis:** 1 vCPU, 1024 MB RAM.
