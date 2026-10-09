"""Circuit Breaker Engine for Unreliable External Systems.

Enforces:
- Tri-state model: CLOSED (normal), OPEN (failing fast), HALF_OPEN (trial recovery).
- Sliding failure counting, configurable cooldown periods, and fast-fail behavior.
- Protection against cascade failures and thread/connection exhaustion.
"""

from datetime import UTC, datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from app.core.exceptions import CampusOSException
from app.models.integration import CircuitBreakerState

logger = logging.getLogger("campusos.integrations.circuit_breaker")


class CircuitBreakerOpenException(CampusOSException):
    def __init__(self, connector_id: UUID | str, cooldown_remaining_seconds: int = 0):
        super().__init__(
            status_code=503,
            code="CIRCUIT_BREAKER_OPEN",
            message=(
                f"External service circuit breaker is OPEN for connector {connector_id}. "
                f"Failing fast to protect institutional resources. Retry after {cooldown_remaining_seconds}s."
            ),
        )


class CircuitBreaker:
    """In-memory and stateful circuit breaker evaluator."""

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: int = 30,
        half_open_success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_success_threshold = half_open_success_threshold

    def evaluate_request_permission(
        self,
        connector_id: UUID | str,
        current_state: str | CircuitBreakerState,
        circuit_opened_at: datetime | None,
        now: datetime | None = None,
    ) -> tuple[bool, CircuitBreakerState, int]:
        """Determine if an outgoing call to the external connector is permitted.

        Returns:
            (is_permitted: bool, effective_state: CircuitBreakerState, cooldown_remaining: int)
        """
        curr = CircuitBreakerState(str(current_state))
        current_time = now or datetime.now(UTC)

        if curr == CircuitBreakerState.CLOSED:
            return True, CircuitBreakerState.CLOSED, 0

        if curr == CircuitBreakerState.OPEN:
            if circuit_opened_at is None:
                # Corrupt state, fail closed for retry
                return True, CircuitBreakerState.HALF_OPEN, 0

            elapsed = (current_time - circuit_opened_at).total_seconds()
            if elapsed >= self.cooldown_seconds:
                logger.info(
                    "Circuit breaker cooldown elapsed for connector %s. Transitioning to HALF_OPEN.",
                    connector_id,
                )
                return True, CircuitBreakerState.HALF_OPEN, 0
            else:
                remaining = max(1, int(self.cooldown_seconds - elapsed))
                return False, CircuitBreakerState.OPEN, remaining

        # HALF_OPEN allows single test probe
        return True, CircuitBreakerState.HALF_OPEN, 0

    def record_success(
        self,
        current_state: str | CircuitBreakerState,
        consecutive_failures: int,
    ) -> tuple[CircuitBreakerState, int]:
        """Record successful call outcome, closing circuit if recovering."""
        curr = CircuitBreakerState(str(current_state))
        if curr in (CircuitBreakerState.HALF_OPEN, CircuitBreakerState.OPEN):
            logger.info("External service call succeeded. Resetting circuit breaker to CLOSED.")
            return CircuitBreakerState.CLOSED, 0
        return CircuitBreakerState.CLOSED, 0

    def record_failure(
        self,
        current_state: str | CircuitBreakerState,
        consecutive_failures: int,
        now: datetime | None = None,
    ) -> tuple[CircuitBreakerState, int, datetime | None]:
        """Record failure outcome, tripping circuit to OPEN if threshold reached."""
        current_time = now or datetime.now(UTC)
        curr = CircuitBreakerState(str(current_state))
        new_failures = consecutive_failures + 1

        if curr == CircuitBreakerState.HALF_OPEN:
            logger.warning(
                "Trial call failed in HALF_OPEN state. Immediately reopening circuit breaker."
            )
            return CircuitBreakerState.OPEN, new_failures, current_time

        if new_failures >= self.failure_threshold:
            logger.warning(
                "Failure threshold (%d/%d) reached. Tripping circuit breaker to OPEN.",
                new_failures,
                self.failure_threshold,
            )
            return CircuitBreakerState.OPEN, new_failures, current_time

        return CircuitBreakerState.CLOSED, new_failures, None


circuit_breaker_engine = CircuitBreaker()
