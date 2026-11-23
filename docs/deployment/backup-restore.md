# CampusOS Database Backup & Restore Verification Runbook

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. Backup Strategy & Policy

To guarantee academic and financial record durability, CampusOS enforces a multi-tiered backup policy:

| Tier | Frequency | Mechanism | Retention | Storage Location |
| :--- | :--- | :--- | :--- | :--- |
| **Full Snapshots** | **Daily at 01:00 UTC** | `pg_dump -Fc` via `scripts/backup.py` | 30 days daily, 12 months monthly | Encrypted Offsite S3 Bucket (`campusos-backups-vault`) |
| **Point-in-Time Recovery (PITR)** | **Continuous** | WAL Archiving / RDS Automated Snapshots | 7 days continuous | Cloud Managed Storage / Multi-AZ |
| **Compliance Archives** | **Annual** | GPG-encrypted immutable tarball | 7 years | S3 Glacier Flexible Archive (Object Lock enabled) |

---

## 2. Backup Execution

### Automated Execution via Script
The production backup script automates compression, checksumming, and metadata generation:

```bash
python scripts/backup.py \
  --db-url "$DATABASE_URL" \
  --output-dir /opt/backups/daily \
  --retention 30
```

### Artifacts Generated per Backup
1. `campusos_campusos_db_20261005_120000.dump`: Custom binary format compressed database dump.
2. `campusos_campusos_db_20261005_120000.dump.sha256`: SHA-256 cryptographic checksum.
3. `campusos_campusos_db_20261005_120000.dump.meta.json`: Machine-readable metadata (database, size, timestamp, commit hash).

---

## 3. Cryptographic Verification

Verify the integrity of any backup file before attempting restoration:

```bash
sha256sum -c campusos_campusos_db_20261005_120000.dump.sha256
```

If the checksum does not match, the backup is considered corrupt and must not be restored.

---

## 4. Automated Restore Verification Pipeline

To ensure backups are not merely generated but actively recoverable, execute the automated restore verification script against an **isolated sandbox database**:

```bash
python scripts/restore_verify.py \
  --backup-file /opt/backups/daily/campusos_campusos_db_latest.dump \
  --sandbox-db campusos_restore_sandbox \
  --host localhost \
  --port 5432 \
  --user campusos_user
```

### Verification Checks Performed
1. **Safety Guardrail:** Validates that `--sandbox-db` does not contain `prod`, `live`, or match the active database.
2. **Integrity Validation:** Verifies SHA-256 checksum against `.sha256` reference.
3. **Database Recreation:** Drops and recreates the isolated sandbox database.
4. **Schema & Data Restoration:** Restores the archive using `pg_restore --no-owner --no-privileges`.
5. **Critical Table Counts:** Queries row counts across `institutions`, `users`, `students`, `courses`, `invoices`, `documents`.
6. **Multi-Tenant Isolation Validation:** Runs query to ensure zero orphan or cross-tenant relationships exist:
   ```sql
   SELECT count(*) FROM students WHERE institution_id NOT IN (SELECT id FROM institutions);
   ```
7. **Scorecard Output:** Outputs `RESTORE VERIFICATION PASSED` upon full confirmation.

---

## 5. Production Disaster Recovery Restoration

In the event of a catastrophic production loss:

1. **Provision New Clean Database:**
   - Stand up a fresh PostgreSQL 16+ instance.
2. **Download Verified Backup & Checksum:**
   - Pull latest backup from offsite S3 vault.
   - Verify SHA-256 checksum.
3. **Execute Restore:**
   ```bash
   pg_restore -h $PROD_DB_HOST -p 5432 -U $PROD_DB_USER -d campusos_db -v --no-owner /opt/backups/verified.dump
   ```
4. **Verify Schema Status:**
   ```bash
   python scripts/migrate.py check
   ```
5. **Run Smoke Tests:**
   ```bash
   python scripts/smoke_test.py --api-url https://api.campus.edu
   ```
