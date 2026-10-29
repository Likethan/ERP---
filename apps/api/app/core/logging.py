import logging
import sys
from contextvars import ContextVar

from app.core.config import settings
from app.core.sanitizer import mask_sensitive_string

# Context variable for request correlation ID across async execution flows
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter generating structured logs with request correlation and sanitized payloads."""

    def format(self, record: logging.LogRecord) -> str:
        # Retrieve correlation ID from contextvar if not explicitly passed
        req_id = correlation_id_ctx.get()
        if not hasattr(record, "correlation_id") or record.correlation_id == "-":
            record.correlation_id = req_id

        # Redact any credentials or secrets in message text
        raw_msg = record.getMessage()
        sanitized_msg = mask_sensitive_string(raw_msg)
        record.msg = sanitized_msg
        record.args = None  # Clear args since msg is already formatted and sanitized

        # Format standardized message
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Configures structured console logging for the application."""
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    formatter = StructuredLogFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [req:%(correlation_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if reloaded
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers[0] = handler

    # Quiet external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.ENVIRONMENT == "development" else logging.WARN
    )

    logger = logging.getLogger("campusos")
    return logger


logger = setup_logging()

