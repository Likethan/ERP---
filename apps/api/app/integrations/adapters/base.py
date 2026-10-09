"""Base Adapter interface for external integration drivers."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.models.integration import IntegrationConnector


class BaseIntegrationAdapter(ABC):
    """Abstract base adapter isolating CampusOS domain from external vendor SDKs."""

    def __init__(self, connector: IntegrationConnector, credentials: dict[str, Any] | None = None):
        self.connector = connector
        self.credentials = credentials or {}
        self.configuration = connector.configuration or {}

    @abstractmethod
    async def ping(self) -> bool:
        """Verify endpoint connectivity and authentication credentials."""
        pass
