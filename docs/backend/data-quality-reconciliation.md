# Automated Data Quality & Operational Reconciliation Engine (Step 28)

## 1. Overview & Principle of Operational Truth

In enterprise university operations, analytical rollups must never drift from the underlying authoritative ledgers. The **Data Quality & Reconciliation Engine** (`app/services/data_quality_reconciliation_service.py`) periodically compares aggregated analytics and analytical summary tables against operational database records.

### Core Philosophy
1. **Zero Silent Fixes**: The reconciliation engine **never** silently alters operational tables (e.g., student balances, invoice totals, or exam scores) to force analytical numbers to align.
2. **Actionable Findings**: Any drift or data anomaly produces an immutable `AnalyticsReconciliationFinding` record with severity, affected metric, exact operational value, analytical value, and percentage variance.
3. **Automated Auditing**: Runs on a scheduled cadence via the background scheduler (`refresh_analytics`) and is available for on-demand inspection by authorized administrators (`POST /api/v1/analytics/reconciliation/run`).

---

## 2. Automated Reconciliation Rules

The engine implements 5 automated reconciliation rules across the operational modules:

### 2.1 `FIN_PAYMENTS_RECONCILIATION`
- **Domain**: Finance & Collections
- **Rule Description**: Compares the sum of successful transactions in `payment_transactions` (`status == 'SUCCESS'`) against the recorded aggregate in `analytics_daily_metrics` for `finance.total_collections`.
- **Severity**:
  - `CRITICAL` if discrepancy $> 0.05\%$
  - `INFO` if perfectly aligned ($0.00\%$)
- **Resolution**: Re-executes historical backfill for the affected tenant if discrepancy is detected, while flagging an audit alert.

### 2.2 `ACAD_STUDENT_STATUS_CONSISTENCY`
- **Domain**: Students & Academics
- **Rule Description**: Scans `student_profiles` for records with missing status, unrecognized status values, or unlinked user accounts.
- **Severity**: `HIGH` if anomalies found.

### 2.3 `ATT_PERCENTAGE_BOUNDARY`
- **Domain**: Attendance
- **Rule Description**: Validates that computed student attendance percentages fall strictly in the closed real interval $[0.0, 100.0]$.
- **Severity**: `CRITICAL` if invalid attendance percentages are detected ($< 0\%$ or $> 100\%$).

### 2.4 `EXAM_MARKS_INTEGRITY`
- **Domain**: Examinations
- **Rule Description**: Scans `student_marks` records to verify that scored marks do not exceed `max_marks` and are non-negative.
- **Severity**: `HIGH` if out-of-boundary scores exist.

### 2.5 `ORPHAN_ATTENDANCE_RECORDS`
- **Domain**: Attendance
- **Rule Description**: Detects attendance records marked for students who are not actively enrolled in the corresponding academic section or course.
- **Severity**: `MEDIUM` if orphaned marks exist.

---

## 3. Data Model (`AnalyticsReconciliationFinding`)

Discrepancies are persisted in `analytics_reconciliation_findings`:

```python
class AnalyticsReconciliationFinding(Base):
    __tablename__ = "analytics_reconciliation_findings"

    id: Mapped[uuid.UUID]
    tenant_id: Mapped[uuid.UUID]
    rule_code: Mapped[str]
    severity: Mapped[str]         # CRITICAL, HIGH, MEDIUM, LOW, INFO
    affected_metric: Mapped[str]
    operational_value: Mapped[Decimal | None]
    analytical_value: Mapped[Decimal | None]
    variance: Mapped[Decimal | None]
    variance_pct: Mapped[Decimal | None]
    details: Mapped[dict | None]
    status: Mapped[str]           # OPEN, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
    detected_at: Mapped[datetime]
    resolved_at: Mapped[datetime | None]
```

---

## 4. Operational API & Endpoints

### 4.1 Trigger On-Demand Reconciliation
```http
POST /api/v1/analytics/reconciliation/run
Authorization: Bearer <token_with_analytics_reconcile>
```
Response:
```json
{
  "scanned_rules_count": 5,
  "findings_count": 0,
  "status": "COMPLETED",
  "executed_at": "2026-10-09T20:30:00Z"
}
```

### 4.2 Query Open Audit Findings
```http
GET /api/v1/analytics/reconciliation?status=OPEN&severity=CRITICAL
Authorization: Bearer <token_with_analytics_reconcile>
```
Response:
```json
[
  {
    "id": "7a3036a5-78e8-466a-b223-10d94726581a",
    "rule_code": "FIN_PAYMENTS_RECONCILIATION",
    "severity": "CRITICAL",
    "affected_metric": "finance.total_collections",
    "operational_value": 520000.00,
    "analytical_value": 515000.00,
    "variance": 5000.00,
    "variance_pct": 0.9615,
    "details": {
      "reason": "Analytical aggregate missing latest confirmed payments batch"
    },
    "status": "OPEN",
    "detected_at": "2026-10-09T18:00:00Z"
  }
]
```

### 4.3 Trigger Historical Backfill
```http
POST /api/v1/analytics/backfill
Authorization: Bearer <token_with_analytics_backfill>
Content-Type: application/json

{
  "domain": "FINANCE",
  "start_date": "2026-01-01",
  "end_date": "2026-10-09"
}
```
Computes and updates `analytics_daily_metrics` directly from authoritative tables, correcting any rollup drift without modifying historical business records.
