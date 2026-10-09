# CampusOS Production Deployment Runbook

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. Overview & Architecture

CampusOS employs a cloud-neutral, containerized production architecture:

```text
                         Internet
                            │
                            ▼
                    DNS / HTTPS / TLS
                            │
                            ▼
                    Reverse Proxy / LB (Nginx)
                     ┌──────┴──────┐
                     │             │
                     ▼             ▼
                Next.js Web     FastAPI API
               (Replicas: 2+)  (Replicas: 2+)
                     │             │
                     │        ┌────┴────┐
                     │        │         │
                     │        ▼         ▼
                     │   PostgreSQL   Redis
                     │        │         │
                     │        │         ▼
                     │        │    Worker / Scheduler
                     │        │
                     │        ▼
                     │   Object Storage (S3 / MinIO)
                     │
                     ▼
                Browser Users
```

---

## 2. Prerequisites

- **Host OS:** Linux (Ubuntu 22.04 LTS recommended) / Docker Engine 24.0+ & Docker Compose v2.20+
- **Database:** PostgreSQL 16+ (Managed RDS/Cloud SQL recommended for production)
- **Cache/Broker:** Redis 7+ (Managed ElastiCache/Memorystore recommended)
- **Object Storage:** S3-compatible bucket (AWS S3, Cloudflare R2, MinIO)
- **Domain & SSL:** Valid domain with TLS certificate (Let's Encrypt / Cloudflare)

---

## 3. First-Time Platform Deployment

Follow this exact sequence to deploy a new production instance from scratch:

### Step 1: Clone Repository & Create Release Directory
```bash
git clone https://github.com/organization/campusos.git /opt/campusos
cd /opt/campusos
git checkout tags/v1.0.0
```

### Step 2: Configure Production Environment Variables
```bash
# Copy production template
cp .env.production.example .env.production

# Edit and supply real cryptographic secrets and production endpoints
nano .env.production
chmod 600 .env.production
```

Ensure the following variables are strictly set:
- `SECRET_KEY`: 32+ character high-entropy random string (`openssl rand -hex 32`)
- `ENVIRONMENT=production`
- `DEBUG=false`
- `DATABASE_URL`: Production PostgreSQL async connection string
- `REDIS_URL`: Production Redis connection string with password/TLS
- `CORS_ORIGINS`: JSON array of explicit domains (`["https://app.campus.edu"]`)
- `STORAGE_ACCESS_KEY` & `STORAGE_SECRET_KEY`: Private S3 credentials

### Step 3: Pull & Build Container Images
```bash
# Using pre-built images from container registry:
docker compose -f docker-compose.prod.yml --env-file .env.production pull

# OR build locally:
docker compose -f docker-compose.prod.yml --env-file .env.production build
```

### Step 4: Verify Database Connectivity & Run Schema Migrations
```bash
# Verify current schema state (does not mutate DB)
python scripts/migrate.py check

# Run forward-only migrations up to current head
python scripts/migrate.py run
```

### Step 5: Provision Initial Platform Administrator
Run the secure administrator bootstrap script:
```bash
python scripts/bootstrap_admin.py \
  --tenant-code CAMPUS_ROOT \
  --tenant-name "Central University" \
  --email "sysadmin@campus.edu"
```
*Secure password will be generated and printed to the terminal once. Save it in the enterprise password vault.*

### Step 6: Start All Services
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### Step 7: Post-Deployment Smoke Verification
```bash
python scripts/smoke_test.py \
  --api-url "https://api.campus.edu" \
  --web-url "https://app.campus.edu"
```

---

## 4. Routine / Zero-Downtime Deployment (CI/CD)

For daily or weekly updates:

1. **GitHub Actions CI Quality Gate:**
   - Lint, Typecheck, Pytest (125 tests), Security Audits, and Next.js builds run automatically on PRs.
2. **Pre-Deployment Backup:**
   - Trigger snapshot backup: `python scripts/backup.py --retention 30`.
3. **Database Migration Step:**
   - Execute backward-compatible migration via `python scripts/migrate.py run`.
4. **Rolling Image Upgrade:**
   - Deploy new API containers replica-by-replica.
   - Deploy new Web containers replica-by-replica.
5. **Post-Deployment Smoke Test:**
   - Automatically execute `scripts/smoke_test.py`.
   - Alert on any non-200 probe.

---

## 5. Rollback Runbook

If a critical fault is discovered post-deployment:

### Application Rollback
```bash
# Roll back container images to previous release tag
export PREVIOUS_TAG=v0.9.8
docker compose -f docker-compose.prod.yml down
# Update image tags in compose or env
docker compose -f docker-compose.prod.yml up -d
```

### Database Schema Rollback Guidelines
- CampusOS requires **additive, backward-compatible migrations** (Expand → Migrate → Contract).
- Old application code must safely function against the new schema.
- **NEVER** run destructive downgrades on active databases.
- If a catastrophic data issue occurred, follow the [Disaster Recovery Runbook](file:///docs/disaster-recovery.md) to restore from the pre-deployment snapshot.
