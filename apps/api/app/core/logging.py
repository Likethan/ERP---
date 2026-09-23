import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured console logging for the application."""
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [req:%(correlation_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        defaults={"correlation_id": "-"},
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
