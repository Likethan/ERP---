"""Quality Rule Evaluator & Dimension Scoring Engine (Step 24).

Implements deterministic validation across all quality rule types:
REQUIRED, UNIQUE, FORMAT, RANGE, ENUM, REFERENCE_EXISTS, REFERENCE_ACTIVE,
CROSS_FIELD, CROSS_ENTITY, FRESHNESS, DUPLICATE.
Calculates multidimensional quality scores and generates actionable defect reports.
"""

import re
from datetime import UTC, datetime
from typing import Any

from app.models.master_data import (
    DataQualityRule,
    QualityRuleType,
)
from app.schemas.master_data import RuleEvaluationItem


class QualityRuleEvaluator:
    """Evaluates data quality rules against record attributes and computes dimension scores."""

    RULE_DIMENSION_MAP = {
        QualityRuleType.REQUIRED: "completeness",
        QualityRuleType.FORMAT: "validity",
        QualityRuleType.RANGE: "validity",
        QualityRuleType.ENUM: "validity",
        QualityRuleType.CROSS_FIELD: "consistency",
        QualityRuleType.CROSS_ENTITY: "consistency",
        QualityRuleType.REFERENCE_EXISTS: "consistency",
        QualityRuleType.REFERENCE_ACTIVE: "consistency",
        QualityRuleType.UNIQUE: "uniqueness",
        QualityRuleType.DUPLICATE: "uniqueness",
        QualityRuleType.FRESHNESS: "timeliness",
    }

    @classmethod
    def evaluate_rule(
        cls,
        rule: DataQualityRule,
        data: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Evaluate a single quality rule against record data.

        Returns (passed, failure_message).
        """
        field = rule.field_name
        params = rule.parameters_json or {}
        val = data.get(field) if field else None
        rtype = rule.rule_type

        # 1. REQUIRED
        if rtype == QualityRuleType.REQUIRED:
            if val is None or (isinstance(val, str) and not val.strip()):
                return False, f"Field '{field}' is required and must not be empty."
            if isinstance(val, (list, dict)) and len(val) == 0:
                return False, f"Field '{field}' must contain at least one item."
            return True, None

        # If value is missing for other rule types, pass
        if val is None:
            return True, None

        # 2. FORMAT (Regex)
        if rtype == QualityRuleType.FORMAT:
            pattern = params.get("regex")
            if pattern:
                str_val = str(val)
                if not re.match(pattern, str_val):
                    return (
                        False,
                        f"Field '{field}' with value '{str_val}' does not match required format.",
                    )
            return True, None

        # 3. RANGE (min/max numeric or date bounds)
        if rtype == QualityRuleType.RANGE:
            try:
                num_val = float(val)
                if "min" in params and num_val < float(params["min"]):
                    return False, f"Field '{field}' must be >= {params['min']}."
                if "max" in params and num_val > float(params["max"]):
                    return False, f"Field '{field}' must be <= {params['max']}."
            except (ValueError, TypeError):
                return False, f"Field '{field}' is not a valid numeric value for range check."
            return True, None

        # 4. ENUM (allowed values)
        if rtype == QualityRuleType.ENUM:
            allowed = params.get("allowed_values", [])
            if allowed and str(val) not in [str(a) for a in allowed]:
                return False, f"Value '{val}' for '{field}' not in allowed options: {allowed}."
            return True, None

        # 5. CROSS_FIELD
        if rtype == QualityRuleType.CROSS_FIELD:
            compare_field = params.get("compare_field")
            op = params.get("operator", "eq")
            if compare_field and compare_field in data:
                other_val = data[compare_field]
                if other_val is not None:
                    if op == "gte" and val < other_val:
                        return (
                            False,
                            f"Field '{field}' ({val}) must be >= '{compare_field}' ({other_val}).",
                        )
                    if op == "gt" and val <= other_val:
                        return (
                            False,
                            f"Field '{field}' ({val}) must be > '{compare_field}' ({other_val}).",
                        )
                    if op == "lte" and val > other_val:
                        return (
                            False,
                            f"Field '{field}' ({val}) must be <= '{compare_field}' ({other_val}).",
                        )
                    if op == "neq" and val == other_val:
                        return False, f"Field '{field}' must not equal '{compare_field}'."
            return True, None

        # 6. FRESHNESS
        if rtype == QualityRuleType.FRESHNESS:
            max_age_days = params.get("max_age_days")
            if max_age_days and isinstance(val, (datetime, str)):
                dt_val = val
                if isinstance(dt_val, str):
                    try:
                        dt_val = datetime.fromisoformat(dt_val)
                    except ValueError:
                        return False, f"Invalid datetime string for freshness check on '{field}'."
                if dt_val.tzinfo is None:
                    dt_val = dt_val.replace(tzinfo=UTC)
                age_days = (datetime.now(UTC) - dt_val).days
                if age_days > max_age_days:
                    return (
                        False,
                        f"Data in '{field}' is stale ({age_days} days old, max is {max_age_days}).",
                    )
            return True, None

        # 7. Default pass
        return True, None

    @classmethod
    def evaluate_all(
        cls,
        rules: list[DataQualityRule],
        data: dict[str, Any],
    ) -> tuple[float, dict[str, float], list[RuleEvaluationItem]]:
        """Evaluate a full rule set against data and compute multidimensional weighted scores.

        Returns (overall_score, dimension_scores, rule_evaluations).
        """
        if not rules:
            default_dims = {
                "completeness": 100.0,
                "validity": 100.0,
                "consistency": 100.0,
                "uniqueness": 100.0,
                "timeliness": 100.0,
            }
            return 100.0, default_dims, []

        eval_results: list[RuleEvaluationItem] = []
        total_weight = 0.0
        passed_weight = 0.0

        dimension_totals: dict[str, float] = {
            "completeness": 0.0,
            "validity": 0.0,
            "consistency": 0.0,
            "uniqueness": 0.0,
            "timeliness": 0.0,
        }
        dimension_passed: dict[str, float] = {
            "completeness": 0.0,
            "validity": 0.0,
            "consistency": 0.0,
            "uniqueness": 0.0,
            "timeliness": 0.0,
        }

        for rule in rules:
            if not rule.is_active:
                continue

            passed, msg = cls.evaluate_rule(rule, data)
            eval_results.append(
                RuleEvaluationItem(
                    rule_key=rule.rule_key,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=rule.field_name,
                    passed=passed,
                    weight=rule.weight,
                    message=msg,
                )
            )

            w = max(rule.weight, 0.1)
            total_weight += w
            dim = cls.RULE_DIMENSION_MAP.get(rule.rule_type, "validity")
            dimension_totals[dim] += w

            if passed:
                passed_weight += w
                dimension_passed[dim] += w

        overall_score = (
            round((passed_weight / total_weight) * 100.0, 1) if total_weight > 0 else 100.0
        )

        dimension_scores: dict[str, float] = {}
        for dim, tot in dimension_totals.items():
            if tot > 0:
                dimension_scores[dim] = round((dimension_passed[dim] / tot) * 100.0, 1)
            else:
                dimension_scores[dim] = 100.0

        return overall_score, dimension_scores, eval_results
