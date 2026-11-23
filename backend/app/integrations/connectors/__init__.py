"""Marketplace Connectors Registry and Factory."""


from app.core.exceptions import ValidationException
from app.integrations.connectors.base import (
    BaseMarketplaceConnector,
    ConnectorBatchResult,
    ConnectorHealthResult,
    ConnectorPushResult,
)
from app.integrations.connectors.biometric import BiometricAttendanceConnector
from app.integrations.connectors.canvas_lms import CanvasLMSConnector
from app.integrations.connectors.moodle_lms import MoodleLMSConnector
from app.integrations.connectors.nad_digilocker import NadDigilockerConnector
from app.integrations.connectors.razorpay import RazorpayConnector
from app.integrations.connectors.zoom import ZoomConnector

_REGISTRY: dict[str, type[BaseMarketplaceConnector]] = {
    "CANVAS_LMS": CanvasLMSConnector,
    "MOODLE_LMS": MoodleLMSConnector,
    "ZOOM_EDUCATION": ZoomConnector,
    "RAZORPAY_CAMPUS": RazorpayConnector,
    "BIOMETRIC_ATTENDANCE": BiometricAttendanceConnector,
    "NAD_DIGILOCKER": NadDigilockerConnector,
}


def get_connector(app_code: str) -> BaseMarketplaceConnector:
    """Retrieve an instantiated connector adapter for the specified marketplace app code."""
    normalized_code = app_code.upper().strip()
    connector_cls = _REGISTRY.get(normalized_code)
    if not connector_cls:
        raise ValidationException(f"Unsupported connector adapter for app code '{app_code}'.")
    return connector_cls()


def list_available_connectors() -> list[str]:
    """Return all registered connector codes."""
    return list(_REGISTRY.keys())


__all__ = [
    "BaseMarketplaceConnector",
    "ConnectorBatchResult",
    "ConnectorHealthResult",
    "ConnectorPushResult",
    "get_connector",
    "list_available_connectors",
    "CanvasLMSConnector",
    "MoodleLMSConnector",
    "ZoomConnector",
    "RazorpayConnector",
    "BiometricAttendanceConnector",
    "NadDigilockerConnector",
]
