"""Connector Execution Framework - Base Contract.

Defines the typed, standardized contract for executing approved marketplace connectors.
All external interactions (Canvas, Moodle, Zoom, Razorpay, Biometric, DigiLocker, etc.)
are governed through this abstract interface, enforcing SSRF safety, timeouts, bounded
retries, credential isolation, and idempotent synchronization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ConnectorHealthResult:
    """Outcome of a live connectivity probe."""

    healthy: bool
    latency_ms: float
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorBatchResult:
    """Batch of records pulled from an external provider."""

    records: list[dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool = False
    error: Optional[str] = None


@dataclass
class ConnectorPushResult:
    """Outcome of pushing a single CampusOS record to an external provider."""

    success: bool
    external_id: Optional[str] = None
    status: str = "SUCCESS"
    error: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


class BaseMarketplaceConnector(ABC):
    """Abstract base connector for all CampusOS marketplace integrations."""

    app_code: str = ""
    app_name: str = ""

    @abstractmethod
    def validate_configuration(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate connection parameters against the app's configuration schema.

        Returns (is_valid, list_of_error_messages).
        """
        pass

    @abstractmethod
    async def test_connectivity(
        self,
        config: dict[str, Any],
        credentials: dict[str, Any],
    ) -> ConnectorHealthResult:
        """Probe the remote service to verify network reachability and credentials."""
        pass

    @abstractmethod
    async def fetch_records(
        self,
        config: dict[str, Any],
        credentials: dict[str, Any],
        entity_type: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> ConnectorBatchResult:
        """Fetch a page of remote records for the specified entity type."""
        pass

    @abstractmethod
    async def push_record(
        self,
        config: dict[str, Any],
        credentials: dict[str, Any],
        entity_type: str,
        payload: dict[str, Any],
    ) -> ConnectorPushResult:
        """Push a CampusOS record to the external system."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
        secret: str,
    ) -> bool:
        """Verify the integrity and authenticity of an inbound webhook event."""
        pass

    @abstractmethod
    def parse_webhook_event(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Parse raw webhook bytes and headers into a normalized event payload."""
        pass
