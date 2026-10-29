"""CampusOS Safe Workflow Condition Evaluation Engine.

Zero eval(), zero exec(), zero arbitrary code execution.
Evaluates structured condition definitions against execution context variables
using an explicit allowlist of operators and type-safe comparisons.
"""

import logging
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from app.core.exceptions import ValidationException

logger = logging.getLogger("campusos.conditions")


class ConditionOperator(StrEnum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT_IN"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    CONTAINS = "CONTAINS"


# Canonical mapping for normalized operator evaluation
_OPERATOR_ALIASES: dict[str, ConditionOperator] = {
    "==": ConditionOperator.EQUALS,
    "eq": ConditionOperator.EQUALS,
    "=": ConditionOperator.EQUALS,
    "!=": ConditionOperator.NOT_EQUALS,
    "neq": ConditionOperator.NOT_EQUALS,
    "<>": ConditionOperator.NOT_EQUALS,
    ">": ConditionOperator.GREATER_THAN,
    "gt": ConditionOperator.GREATER_THAN,
    ">=": ConditionOperator.GREATER_THAN_OR_EQUAL,
    "gte": ConditionOperator.GREATER_THAN_OR_EQUAL,
    "<": ConditionOperator.LESS_THAN,
    "lt": ConditionOperator.LESS_THAN,
    "<=": ConditionOperator.LESS_THAN_OR_EQUAL,
    "lte": ConditionOperator.LESS_THAN_OR_EQUAL,
    "in": ConditionOperator.IN,
    "IN": ConditionOperator.IN,
    "not_in": ConditionOperator.NOT_IN,
    "NOT_IN": ConditionOperator.NOT_IN,
    "is_null": ConditionOperator.IS_NULL,
    "IS_NULL": ConditionOperator.IS_NULL,
    "is_not_null": ConditionOperator.IS_NOT_NULL,
    "IS_NOT_NULL": ConditionOperator.IS_NOT_NULL,
    "contains": ConditionOperator.CONTAINS,
    "CONTAINS": ConditionOperator.CONTAINS,
}


def _resolve_nested_field(context: dict[str, Any], path: str) -> Any:
    """Safely extracts field values from context using dot notation without eval."""
    parts = path.split(".")
    curr: Any = context
    for part in parts:
        if isinstance(curr, dict):
            curr = curr.get(part)
        elif hasattr(curr, part) and not part.startswith("_"):
            curr = getattr(curr, part)
        else:
            return None
        if curr is None:
            return None
    return curr


def _compare_values(actual: Any, op: ConditionOperator, expected: Any) -> bool:
    """Safely compare actual context value against expected value with typed operators."""
    if op == ConditionOperator.IS_NULL:
        return actual is None

    if op == ConditionOperator.IS_NOT_NULL:
        return actual is not None

    if actual is None:
        return False

    if op == ConditionOperator.EQUALS:
        return actual == expected

    if op == ConditionOperator.NOT_EQUALS:
        return actual != expected

    if op == ConditionOperator.CONTAINS:
        if isinstance(actual, (str, list, tuple, set, dict)):
            return expected in actual
        return False

    if op == ConditionOperator.IN:
        if isinstance(expected, (list, tuple, set)):
            return actual in expected
        return False

    if op == ConditionOperator.NOT_IN:
        if isinstance(expected, (list, tuple, set)):
            return actual not in expected
        return True

    # Numeric comparisons
    try:
        act_num = float(actual) if not isinstance(actual, bool) else (1.0 if actual else 0.0)
        exp_num = float(expected) if not isinstance(expected, bool) else (1.0 if expected else 0.0)
    except (ValueError, TypeError):
        # Fallback to direct string/type comparison if not coercible to numbers
        act_num, exp_num = actual, expected

    try:
        if op == ConditionOperator.GREATER_THAN:
            return act_num > exp_num
        if op == ConditionOperator.GREATER_THAN_OR_EQUAL:
            return act_num >= exp_num
        if op == ConditionOperator.LESS_THAN:
            return act_num < exp_num
        if op == ConditionOperator.LESS_THAN_OR_EQUAL:
            return act_num <= exp_num
    except TypeError:
        return False

    return False


class ConditionEngine:
    """Safe evaluation and validation engine for workflow condition nodes."""

    @classmethod
    def validate_condition_structure(cls, condition: Any) -> None:
        """Validate condition specification schema before workflow can be saved or activated."""
        if condition is None:
            return

        if not isinstance(condition, dict):
            raise ValidationException("Workflow condition must be a JSON object.")

        # Check for logical grouping: "all" (AND) or "any" (OR)
        if "all" in condition:
            sub = condition["all"]
            if not isinstance(sub, Sequence) or isinstance(sub, str):
                raise ValidationException("Condition 'all' must be a list of condition objects.")
            for item in sub:
                cls.validate_condition_structure(item)
            return

        if "any" in condition:
            sub = condition["any"]
            if not isinstance(sub, Sequence) or isinstance(sub, str):
                raise ValidationException("Condition 'any' must be a list of condition objects.")
            for item in sub:
                cls.validate_condition_structure(item)
            return

        # Single condition rule: field, operator, value
        if "field" not in condition:
            raise ValidationException("Condition rule missing required 'field' property.")

        field = condition["field"]
        if not isinstance(field, str) or not field.strip() or " " in field:
            raise ValidationException(f"Invalid field name '{field}' in condition.")

        # Disallow dangerous dunder access
        if "__" in field:
            raise ValidationException("Dunder '__' attribute access is forbidden in condition fields.")

        raw_op = condition.get("operator")
        if not raw_op or str(raw_op) not in _OPERATOR_ALIASES:
            allowed = ", ".join(sorted(list({op.value for op in ConditionOperator})))
            raise ValidationException(f"Unsupported operator '{raw_op}'. Allowed: {allowed}")

        op = _OPERATOR_ALIASES[str(raw_op)]
        if op not in (ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL) and "value" not in condition:
            raise ValidationException(f"Condition operator '{op.value}' requires a 'value' property.")

    @classmethod
    def evaluate(cls, condition: dict[str, Any] | None, context: dict[str, Any]) -> bool:
        """Evaluate condition against execution context. Returns True if passed or if condition is None."""
        if condition is None or not condition:
            return True

        if "all" in condition:
            rules = condition["all"]
            return all(cls.evaluate(r, context) for r in rules)

        if "any" in condition:
            rules = condition["any"]
            return any(cls.evaluate(r, context) for r in rules)

        field = condition.get("field")
        if not field:
            return True

        raw_op = condition.get("operator", "==")
        op = _OPERATOR_ALIASES.get(str(raw_op))
        if not op:
            logger.warning("Unrecognized operator '%s' evaluated to False", raw_op)
            return False

        expected = condition.get("value")
        actual = _resolve_nested_field(context, field)

        result = _compare_values(actual, op, expected)
        logger.debug(
            "Condition evaluated [%s %s %s]: actual=%r -> %s",
            field, op.value, expected, actual, result
        )
        return result
