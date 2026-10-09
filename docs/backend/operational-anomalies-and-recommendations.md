# Operational Forecasting, Anomaly Detection & Recommendation Engine

## 1. Operational Anomaly Detection (`OperationalAnomalyService`)

CampusOS monitors campus operational telemetry and financial transactions to identify deviations before they impact institutional health:

### Scanned Domains & Methods:
1. **Attendance Trends (`ATTENDANCE`)**:
   - Detects class-wide or department-wide sudden drops in session attendance compared against 30-day baseline moving averages.
2. **Fee Collection Flow (`FINANCE`)**:
   - Compares daily confirmed fee inflows (`finance_payments`) against expected seasonal collections baselines.
   - Flags collection anomalies exceeding $\pm 2.0$ standard deviations without asserting fraud.
3. **Campus Operations (`OPERATIONS`)**:
   - Evaluates hostel occupancy rates and facility ticket resolution times.

All anomalies are emitted as formal `Alert` records (`app/models/intelligence.py`) linked to the tenant and available for acknowledgment (`ACKNOWLEDGED`), dismissal (`DISMISSED`), or escalation by authorized staff.

---

## 2. Evidence-Based Recommendation Engine (`RecommendationEngine`)

The recommendation engine (`app/domains/intelligence/services/recommendation_service.py`) generates actionable advice backed by domain metrics:

### Core Recommendation Fields:
- `recommendation_id`: Human-readable identifier (e.g., `REC-ATT-DEFICIT-001`).
- `category`: `ACADEMIC_SUPPORT`, `FINANCE_OPTIMIZATION`, `OPERATIONAL_ALERT`.
- `title` & `reasoning_summary`: Concise, explainable summary of observed patterns.
- `metric_references`: Traceable links to Governed Metric Registry keys (e.g., `attendance.average_percentage`, `finance.total_collections`).
- `suggested_action`: Prescribed next step.
- `status`: Lifecycle status (`PENDING_REVIEW`, `ACTIONED`, `DISMISSED`).

---

## 3. Human-in-the-Loop Case Management Integration

Recommendations do not autonomously alter academic or financial records. Instead, CampusOS allows authorized decision-makers to convert a recommendation into an authoritative Case:

1. **User Action**:
   Staff executes `POST /api/v1/intelligence/recommendations/{id}/action` with payload:
   ```json
   {
     "action": "CONVERT_TO_CASE",
     "notes": "Senate approved student mentoring case."
   }
   ```
2. **Case Creation**:
   The engine creates an authoritative record in `Case` (`app/models/case_management.py`) with:
   - `case_type_code = "AI_RECOMMENDED_ACTION"`
   - `created_by_id = current_user.id`
   - `tenant_id = tenant.tenant_id`
3. **Audit Trail**:
   The recommendation's `workflow_case_id` is updated, creating a permanent bidirectional link between AI suggestion and administrative follow-through.
