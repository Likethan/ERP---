"""Deterministic, Safe Business Policy Condition Evaluator for CampusOS (Step 23)."""

from typing import Any


class PolicyEvaluator:
    """Evaluates declarative business policy rules safely without dynamic scripting or eval()."""

    SUPPORTED_OPERATORS = {
        "eq",
        "neq",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "not_in",
        "contains",
        "between",
    }

    @classmethod
    def evaluate_condition(cls, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        field = condition.get("field")
        operator = condition.get("operator", "eq").lower()
        if operator in ("equals", "=="):
            operator = "eq"
        elif operator in ("not_equals", "!="):
            operator = "neq"
        target = condition.get("value")

        if field not in context:
            return False

        actual = context[field]

        try:
            if operator == "eq":
                return actual == target
            elif operator == "neq":
                return actual != target
            elif operator == "gt":
                return actual > target
            elif operator == "gte":
                return actual >= target
            elif operator == "lt":
                return actual < target
            elif operator == "lte":
                return actual <= target
            elif operator == "in":
                return actual in target if isinstance(target, (list, tuple, set)) else False
            elif operator == "not_in":
                return actual not in target if isinstance(target, (list, tuple, set)) else True
            elif operator == "contains":
                if isinstance(actual, (list, tuple, set, str)):
                    return target in actual
                return False
            elif operator == "between":
                if isinstance(target, (list, tuple)) and len(target) == 2:
                    return target[0] <= actual <= target[1]
                return False
        except Exception:
            return False

        return False

    @classmethod
    def evaluate_policy_rules(
        cls,
        conditions: list[dict[str, Any]],
        context: dict[str, Any],
        logic: str = "all",
    ) -> tuple[bool, int]:
        """Evaluate a list of declarative condition rules against operational context.

        Returns (decision: bool, matched_count: int).
        """
        if not conditions:
            # Policy with empty conditions evaluates to true
            return True, 0

        matched_count = 0
        for cond in conditions:
            if cls.evaluate_condition(cond, context):
                matched_count += 1

        if logic == "any":
            decision = matched_count > 0
        else:
            decision = matched_count == len(conditions)

        return decision, matched_count
