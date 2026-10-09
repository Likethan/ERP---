# Data Quality Engine & Scoring Architecture

CampusOS incorporates an automated, deterministic Data Quality engine that continuously monitors institutional master records across six quality dimensions.

---

## 1. Six Quality Dimensions

Every master record is evaluated against measurable, weighted dimensions:

1. **Completeness**: Required operational fields are present and non-empty.
2. **Validity**: Values conform strictly to semantic formats, patterns (regex), and bounds (ranges/enums).
3. **Consistency**: Cross-field logical requirements do not conflict (e.g. graduation date after admission date).
4. **Uniqueness**: Identifier values (e.g. admission numbers, department codes) are unique within the tenant.
5. **Timeliness (Freshness)**: Records and status updates are within acceptable freshness age windows.
6. **Referential Integrity**: Foreign references point to existing, active institutional records.

---

## 2. Configurable Quality Rules

Rules are managed in `data_quality_rules` and scoped to a tenant and master entity:

### Supported Rule Types

- `REQUIRED`: Non-null and non-empty check.
- `UNIQUE`: Collision check across all tenant records for the field.
- `FORMAT`: Regex pattern compliance (e.g. email, phone, URL).
- `RANGE`: Numerical or date bounds validation (`min`, `max`).
- `ENUM`: Whitelist membership check against allowed codes.
- `REFERENCE_EXISTS`: Target foreign record exists in canonical table.
- `REFERENCE_ACTIVE`: Target foreign record has `is_active = True`.
- `CROSS_FIELD`: Conditional consistency between related fields.
- `FRESHNESS`: Days elapsed since `updated_at` within maximum age limit.
- `DUPLICATE`: Flagged candidate collision threshold evaluation.

### Severities & Scoring Penalties

| Severity | Description | Weight Penalty Multiplier |
|---|---|---|
| `INFO` | Informational advisory note | 0.25 |
| `WARNING` | Non-fatal anomaly (e.g. unverified phone) | 0.50 |
| `ERROR` | Severe deficiency (e.g. missing required field) | 1.00 |
| `CRITICAL` | Fatal integrity breach (e.g. duplicate key) | 2.00 |

---

## 3. Deterministic Scoring Algorithm

Scores are computed deterministically per dimension and aggregated into an `overall_score`:

```python
dimension_score = max(0.0, 100.0 - (dimension_penalties / dimension_weight * 100.0))
overall_score = sum(dimension_scores[dim] * dimension_weights[dim])
```

Default dimension weights:
- Completeness: 25%
- Validity: 25%
- Uniqueness: 20%
- Consistency: 15%
- Timeliness: 15%

---

## 4. Historical Snapshots & Results Storage

- Evaluation snapshots are stored in `data_quality_results`.
- Stores `overall_score`, `dimension_scores_json`, and detailed `rule_results_json`.
- Retains evaluation timestamp and rule versions for historical audits.
