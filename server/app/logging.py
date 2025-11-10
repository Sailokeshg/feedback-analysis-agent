"""
Structured logging configuration using loguru with JSON formatting.
"""
import sys
import os
from contextvars import ContextVar
from typing import Any, Dict
import json
from datetime import datetime

from loguru import logger
from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    """Settings for logging configuration."""

    log_level: str = "INFO"
    json_logs: bool = True
    log_file: str = "logs/app.log"
    log_rotation: str = "10 MB"
    log_retention: str = "1 week"

    class Config:
        env_prefix = "LOG_"


# Context variables for request tracking
request_id: ContextVar[str] = ContextVar('request_id', default="")
user_id: ContextVar[str] = ContextVar('user_id', default="")
correlation_id: ContextVar[str] = ContextVar('correlation_id', default="")


def json_formatter(record: Dict[str, Any]) -> str:
    """Format log records as JSON with structured data."""
    # Extract standard fields
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": record["level"].name,
        "message": record["message"],
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add request context if available
    try:
        if request_id.get():
            log_entry["request_id"] = request_id.get()
        if user_id.get():
            log_entry["user_id"] = user_id.get()
        if correlation_id.get():
            log_entry["correlation_id"] = correlation_id.get()
    except LookupError:
        # Context variables not set
        pass

    # Add extra fields from record
    if "extra" in record:
        for key, value in record["extra"].items():
            # Skip sensitive fields or convert to safe types
            if key not in ["password", "token", "secret"]:
                log_entry[key] = value

    # Add exception info if present
    if record.get("exception"):
        log_entry["exception"] = {
            "type": record["exception"].type.__name__,
            "message": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return json.dumps(log_entry, default=str)


def text_formatter(record: Dict[str, Any]) -> str:
    """Format log records as human-readable text."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    level = record["level"].name
    message = record["message"]
    module = record["module"]
    function = record["function"]

    # Build context string
    context_parts = []
    try:
        if request_id.get():
            context_parts.append(f"req:{request_id.get()[:8]}")
        if user_id.get():
            context_parts.append(f"user:{user_id.get()}")
        if correlation_id.get():
            context_parts.append(f"corr:{correlation_id.get()[:8]}")
    except LookupError:
        pass

    context = f" [{' '.join(context_parts)}]" if context_parts else ""

    return f"{timestamp} {level} {module}.{function}{context} - {message}"


def setup_logging(settings: LoggingSettings = None) -> None:
    """Configure loguru with structured logging."""
    if settings is None:
        settings = LoggingSettings()

    # Remove default handler
    logger.remove()

    # Determine format based on settings
    formatter = json_formatter if settings.json_logs else text_formatter

    # Add console handler using a sink function to avoid Loguru format parsing
    def _console_sink(message):
        try:
            out = formatter(message.record)
        except Exception:
            out = message.record.get("message", "")
        # Ensure a newline
        sys.stdout.write(out + "\n")

    logger.add(
        _console_sink,
        level=settings.log_level,
        colorize=not settings.json_logs,
    )

    # Add file handler if configured
    if settings.log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # File sink: write JSON lines. We use a simple sink function so we can
        # control formatting and avoid Loguru's internal format parsing.
        def _file_sink(message):
            try:
                out = json_formatter(message.record)
            except Exception:
                out = message.record.get("message", "")
            with open(settings.log_file, "a", encoding="utf-8") as f:
                f.write(out + "\n")

        logger.add(
            _file_sink,
            level=settings.log_level,
        )

    # Configure third-party loggers to use our logger
    import logging
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("fastapi").handlers = []

    # Add handlers for third-party loggers to redirect to loguru
    class LoguruHandler(logging.Handler):
        def emit(self, record):
            try:
                # Use the Loguru logger to handle formatting via our sinks
                logger.log(record.levelname, record.getMessage())
            except Exception:
                # Fallback to a minimal write to stderr to avoid crashing
                try:
                    sys.stderr.write(record.getMessage() + "\n")
                except Exception:
                    pass

    # Apply to common loggers
    for log_name in ["uvicorn", "uvicorn.access", "fastapi", "sqlalchemy"]:
        logging.getLogger(log_name).addHandler(LoguruHandler())
        logging.getLogger(log_name).setLevel(settings.log_level)


def get_logger(name: str):
    """Get a logger instance with the specified name."""
    return logger.bind(logger_name=name)


def set_request_context(request_id_val: str = "", user_id_val: str = "", correlation_id_val: str = ""):
    """Set context variables for the current request."""
    if request_id_val:
        request_id.set(request_id_val)
    if user_id_val:
        user_id.set(user_id_val)
    if correlation_id_val:
        correlation_id.set(correlation_id_val)


def clear_request_context():
    """Clear request context variables."""
    try:
        request_id.set("")
        user_id.set("")
        correlation_id.set("")
    except LookupError:
        pass


# Create a default logger instance
log = logger.bind(logger_name="app")
