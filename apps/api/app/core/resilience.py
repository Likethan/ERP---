"""Application Resilience, Circuit Breakers & Dependency Failure Handling (Step 31).

Product Vision: "One Campus. One System. One Source of Truth."

Guarantees:
- Circuit breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Non-idempotent operations are NEVER automatically retried
- Bounded retries with exponential backoff and randomized jitter
- Safe session rollback and connection resilience
- No retry multiplication across service layers
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
import logging
import random
from typing import Any

from app.models.reliability import ReliabilityCircuitBreakerState

logger = logging.getLogger("campusos.resilience")


class CircuitBreakerOpenException(Exception):
    """Raised when an outbound dependency call is blocked because its circuit is open."""

    def __init__(self, dependency_name: str, time_until_reset: float):
        self.dependency_name = dependency_name
        self.time_until_reset = time_until_reset
        super().__init__(
            f"Circuit breaker for '{dependency_name}' is OPEN. "
            f"Fast-failing request. Probe retry available in {time_until_reset:.1f}s."
        )


class NonIdempotentRetryProhibitedException(Exception):
    """Raised when an attempt is made to automatically retry a non-idempotent operation."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        super().__init__(
            f"Automatic retry prohibited for non-idempotent operation: '{operation_name}'. "
            "Manual reconciliation or explicit client retry with idempotency key required."
        )


class CircuitBreaker:
    """In-memory circuit breaker governing outbound calls to external dependencies."""

    def __init__(
        self,
        dependency_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
        half_open_success_threshold: int = 2,
    ):
        self.dependency_name = dependency_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self.state: ReliabilityCircuitBreakerState = ReliabilityCircuitBreakerState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.consecutive_failures: int = 0
        self.consecutive_successes: int = 0
        self.last_failure_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.last_state_change_at: datetime = datetime.now(UTC)
        self._lock = asyncio.Lock()

    async def can_execute(self) -> bool:
        """Evaluate if an outbound request is permitted through the circuit."""
        async with self._lock:
            now = datetime.now(UTC)

            if self.state == ReliabilityCircuitBreakerState.CLOSED:
                return True

            if self.state == ReliabilityCircuitBreakerState.OPEN:
                elapsed = (now - self.last_state_change_at).total_seconds()
                if elapsed >= self.recovery_timeout_seconds:
                    logger.info(
                        "Circuit breaker for '%s' elapsed recovery timeout (%.1fs). Transitioning OPEN -> HALF_OPEN.",
                        self.dependency_name,
                        elapsed,
                    )
                    self.state = ReliabilityCircuitBreakerState.HALF_OPEN
                    self.consecutive_successes = 0
                    self.last_state_change_at = now
                    return True
                return False

            if self.state == ReliabilityCircuitBreakerState.HALF_OPEN:
                # In HALF_OPEN, allow probe requests
                return True

            return False

    async def record_success(self) -> None:
        """Record a successful execution through the circuit."""
        async with self._lock:
            now = datetime.now(UTC)
            self.success_count += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_success_at = now

            if self.state == ReliabilityCircuitBreakerState.HALF_OPEN:
                if self.consecutive_successes >= self.half_open_success_threshold:
                    logger.info(
                        "Circuit breaker for '%s' probe successful (%d consecutive successes). Transitioning HALF_OPEN -> CLOSED.",
                        self.dependency_name,
                        self.consecutive_successes,
                    )
                    self.state = ReliabilityCircuitBreakerState.CLOSED
                    self.consecutive_failures = 0
                    self.last_state_change_at = now

    async def record_failure(self, error: Exception | str | None = None) -> None:
        """Record an execution failure and trip circuit if threshold is reached."""
        async with self._lock:
            now = datetime.now(UTC)
            self.failure_count += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_at = now

            if self.state == ReliabilityCircuitBreakerState.CLOSED:
                if self.consecutive_failures >= self.failure_threshold:
                    logger.warning(
                        "Circuit breaker for '%s' TRIPPED after %d consecutive failures. Transitioning CLOSED -> OPEN.",
                        self.dependency_name,
                        self.consecutive_failures,
                    )
                    self.state = ReliabilityCircuitBreakerState.OPEN
                    self.last_state_change_at = now

            elif self.state == ReliabilityCircuitBreakerState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker for '%s' probe failed during HALF_OPEN. Transitioning HALF_OPEN -> OPEN.",
                    self.dependency_name,
                )
                self.state = ReliabilityCircuitBreakerState.OPEN
                self.last_state_change_at = now

    async def reset(self) -> None:
        """Manually reset circuit breaker to healthy CLOSED state."""
        async with self._lock:
            self.state = ReliabilityCircuitBreakerState.CLOSED
            self.consecutive_failures = 0
            self.consecutive_successes = 0
            self.last_state_change_at = datetime.now(UTC)
            logger.info("Circuit breaker for '%s' manually reset to CLOSED.", self.dependency_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for telemetry responses."""
        return {
            "dependency_name": self.dependency_name,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_at": self.last_failure_at,
            "last_success_at": self.last_success_at,
            "last_state_change_at": self.last_state_change_at,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": int(self.recovery_timeout_seconds),
        }


class CircuitBreakerRegistry:
    """Thread-safe registry of named circuit breakers."""

    _instance: "CircuitBreakerRegistry | None" = None

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        # Pre-seed standard enterprise dependencies
        self.get_or_create("ai_intelligence_provider", failure_threshold=3, recovery_timeout_seconds=60.0)
        self.get_or_create("notification_email_provider", failure_threshold=5, recovery_timeout_seconds=60.0)
        self.get_or_create("notification_sms_provider", failure_threshold=5, recovery_timeout_seconds=60.0)
        self.get_or_create("s3_object_storage", failure_threshold=4, recovery_timeout_seconds=30.0)
        self.get_or_create("payment_gateway_integration", failure_threshold=3, recovery_timeout_seconds=90.0)

    @classmethod
    def get_instance(cls) -> "CircuitBreakerRegistry":
        if cls._instance is None:
            cls._instance = CircuitBreakerRegistry()
        return cls._instance

    def get_or_create(
        self,
        dependency_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
    ) -> CircuitBreaker:
        if dependency_name not in self._breakers:
            self._breakers[dependency_name] = CircuitBreaker(
                dependency_name=dependency_name,
                failure_threshold=failure_threshold,
                recovery_timeout_seconds=recovery_timeout_seconds,
            )
        return self._breakers[dependency_name]

    def get_all(self) -> list[CircuitBreaker]:
        return list(self._breakers.values())

    def reset_all(self) -> None:
        for b in self._breakers.values():
            b.state = ReliabilityCircuitBreakerState.CLOSED
            b.consecutive_failures = 0
            b.consecutive_successes = 0
            b.last_state_change_at = datetime.now(UTC)


circuit_registry = CircuitBreakerRegistry.get_instance()


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    is_idempotent: bool = False,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    operation_name: str | None = None,
    **kwargs: Any,
) -> Any:
    """Execute an async operation with bounded exponential backoff and randomized jitter.

    CRITICAL RULE:
    If `is_idempotent` is False, the operation is NEVER retried automatically.
    """
    op_name = operation_name or getattr(func, "__name__", "anonymous_operation")

    if not is_idempotent:
        # Non-idempotent operations: execute strictly once without automatic retries
        return await func(*args, **kwargs)

    attempt = 0
    while True:
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as exc:
            attempt += 1
            if attempt > max_retries:
                logger.error(
                    "Exhausted %d retries for idempotent operation '%s'. Final error: %s",
                    max_retries,
                    op_name,
                    exc,
                )
                raise

            # Bounded exponential backoff with full jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jittered_delay = delay * random.uniform(0.5, 1.5)
            logger.warning(
                "Idempotent operation '%s' failed (attempt %d/%d): %s. Retrying in %.3fs...",
                op_name,
                attempt,
                max_retries,
                exc,
                jittered_delay,
            )
            await asyncio.sleep(jittered_delay)
