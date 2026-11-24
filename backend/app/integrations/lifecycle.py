"""Connector Lifecycle State Machine and Transition Guard.

Enforces:
- Deterministic lifecycle states: DRAFT, CONFIGURED, ACTIVE, PAUSED, ERROR, DISABLED, REVOKED.
- Strict transition validation preventing invalid or corrupt state mutations.
- Controlled 409 ConflictException on unauthorized state changes.
"""

from typing import Final

from app.core.exceptions import ConflictException
from app.models.integration import ConnectorStatus

VALID_CONNECTOR_TRANSITIONS: Final[dict[ConnectorStatus, frozenset[ConnectorStatus]]] = {
    ConnectorStatus.DRAFT: frozenset({
        ConnectorStatus.CONFIGURED,
        ConnectorStatus.DISABLED,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.CONFIGURED: frozenset({
        ConnectorStatus.ACTIVE,
        ConnectorStatus.DRAFT,
        ConnectorStatus.DISABLED,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.ACTIVE: frozenset({
        ConnectorStatus.PAUSED,
        ConnectorStatus.ERROR,
        ConnectorStatus.DISABLED,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.PAUSED: frozenset({
        ConnectorStatus.ACTIVE,
        ConnectorStatus.DISABLED,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.ERROR: frozenset({
        ConnectorStatus.CONFIGURED,
        ConnectorStatus.ACTIVE,
        ConnectorStatus.DISABLED,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.DISABLED: frozenset({
        ConnectorStatus.CONFIGURED,
        ConnectorStatus.ACTIVE,
        ConnectorStatus.REVOKED,
    }),
    ConnectorStatus.REVOKED: frozenset(),  # Terminal state: cannot be transitioned
}


class ConnectorLifecycleManager:
    """Validates and applies connector lifecycle state transitions."""

    @classmethod
    def can_transition(cls, current_status: str | ConnectorStatus, target_status: str | ConnectorStatus) -> bool:
        """Check if transition from current to target is allowed."""
        curr = ConnectorStatus(str(current_status))
        target = ConnectorStatus(str(target_status))
        if curr == target:
            return True
        allowed = VALID_CONNECTOR_TRANSITIONS.get(curr, frozenset())
        return target in allowed

    @classmethod
    def validate_transition(
        cls,
        current_status: str | ConnectorStatus,
        target_status: str | ConnectorStatus,
        connector_name: str = "Connector",
    ) -> ConnectorStatus:
        """Validate state transition or raise 409 ConflictException."""
        curr = ConnectorStatus(str(current_status))
        target = ConnectorStatus(str(target_status))

        if curr == target:
            return target

        allowed = VALID_CONNECTOR_TRANSITIONS.get(curr, frozenset())
        if target not in allowed:
            allowed_names = ", ".join(sorted([s.value for s in allowed])) or "None (Terminal State)"
            raise ConflictException(
                f"Invalid lifecycle transition for {connector_name}: cannot change from '{curr.value}' to '{target.value}'. "
                f"Allowed transitions from '{curr.value}': [{allowed_names}]."
            )
        return target
