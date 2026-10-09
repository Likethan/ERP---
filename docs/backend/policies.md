# Business Policy Engine

The **Business Policy Engine** provides a deterministic, auditable rule evaluation system that decouples business thresholds, approval logic, and eligibility gates from application code.

---

## 1. Architectural Principles

- **Deterministic Evaluation**: Policy rules are evaluated using a strictly whitelisted set of operators. Arbitrary code execution, dynamic `eval()`, and raw SQL queries are prohibited.
- **Tenant-Scoped Rules**: Policies are partitioned by `tenant_id`. Policies can optionally target institutions, campuses, or modules.
- **Priority & Precedence**: If multiple policies match a given evaluation key, policies are evaluated in descending order of `priority`. The first matching policy determines the decision.
- **Version Tracking**: Every change to policy conditions or actions generates an immutable record in `configuration_policy_versions`.
- **Structured Decision Output**: Evaluation produces a standardized decision payload containing:
  - `matched`: Boolean indicating if conditions were satisfied.
  - `decision`: True/False outcome or configured decision action.
  - `actions`: Structured action definitions (e.g., alert triggers, status overrides).
  - `matched_policy_id`: ID of the policy applied.
  - `version`: Version number of the evaluated policy.

---

## 2. Supported Condition Operators

The policy condition evaluator inspects fields from the evaluation context dictionary:

| Operator | Syntax | Description | Example |
|---|---|---|---|
| `eq` | `{"field": "status", "operator": "eq", "value": "ACTIVE"}` | Value equals expected | Context `status == "ACTIVE"` |
| `neq` | `{"field": "risk", "operator": "neq", "value": "HIGH"}` | Value does not equal expected | Context `risk != "HIGH"` |
| `gt` | `{"field": "percentage", "operator": "gt", "value": 75.0}` | Greater than | Context `percentage > 75.0` |
| `gte` | `{"field": "gpa", "operator": "gte", "value": 3.0}` | Greater than or equal | Context `gpa >= 3.0` |
| `lt` | `{"field": "balance", "operator": "lt", "value": 0}` | Less than | Context `balance < 0` |
| `lte` | `{"field": "attendance", "operator": "lte", "value": 60.0}` | Less than or equal | Context `attendance <= 60.0` |
| `in` | `{"field": "tier", "operator": "in", "value": ["A", "B"]}` | Context value is member of list | Context `tier in ["A", "B"]` |
| `not_in`| `{"field": "state", "operator": "not_in", "value": ["SUSPENDED"]}` | Context value is not in list | Context `state not in list` |
| `contains` | `{"field": "tags", "operator": "contains", "value": "HONORS"}` | List in context contains item | `"HONORS" in context["tags"]` |
| `between` | `{"field": "score", "operator": "between", "value": [60, 80]}` | Context value within closed interval | `60 <= context["score"] <= 80` |

If all conditions in `conditions["all"]` evaluate to `True`, the policy condition succeeds.

---

## 3. Policy Evaluation Workflow

```python
from app.services.policy_service import PolicyService

policy_service = PolicyService(db_session)
result = await policy_service.evaluate_policy(
    policy_key="attendance.low_attendance_threshold",
    context={
        "attendance_percentage": 58.5,
        "is_medical_leave": False,
        "semester": 4
    },
    tenant_id=tenant_id,
    institution_id=institution_id,
)

if result.matched:
    # Trigger low attendance alert or examination bar action
    apply_actions(result.actions)
```

---

## 4. Operational Policies vs Approval Policies

1. **Operational Policies**:
   - `attendance.low_attendance_threshold`: Flags students below the required minimum attendance.
   - `examination.minimum_pass_percentage`: Evaluates passing eligibility for course assessments.
   - `finance.invoice.overdue_after_days`: Flags invoices for penalty or overdue notifications.
   - `placement.maximum_active_applications`: Limits student applications to open placement drives.

2. **Approval Policies**:
   - Integrates with the CampusOS Workflow Engine.
   - Evaluates whether transactions require single-tier or multi-tier approval:
     - Fee concession requests exceeding configured threshold.
     - Grade modifications post-publication.
     - Document de-duplication or manual verification.
     - High-impact configuration changes (e.g. changing institution currency or fiscal year).
