"""Logging configuration for production."""
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configure application logging for production.
    
    Sets up structured logging with appropriate levels and formats.
    """
    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
