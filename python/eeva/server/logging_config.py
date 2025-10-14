import json
import logging
import sys
import traceback
from typing import Any, Dict


class SingleLineFormatter(logging.Formatter):
    """Custom formatter that ensures all log entries are single lines."""

    def format(self, record: logging.LogRecord) -> str:
        # Get the original formatted message
        message = super().format(record)

        # Handle exceptions by converting traceback to single line
        if record.exc_info:
            exc_text = traceback.format_exception(*record.exc_info)
            # Join all traceback lines with literal \n for single-line output
            record.exc_text = "\\n".join(line.rstrip() for line in exc_text)

        # Replace actual newlines with literal \n
        message = message.replace("\n", "\\n").replace("\r", "\\r")

        return message


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs for Cloud Run."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            exc_text = traceback.format_exception(*record.exc_info)
            log_entry["exception"] = "\\n".join(line.rstrip() for line in exc_text)

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                log_entry[key] = value

        # Ensure the JSON is on a single line
        return json.dumps(log_entry, ensure_ascii=False, separators=(",", ":"))


def setup_logging() -> None:
    """Configure logging for Cloud Run deployment."""

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Use structured JSON formatter for Cloud Run
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    # Set up specific loggers
    logging.getLogger("eeva").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)


def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """Helper function to log exceptions with context."""
    logger.error(message, exc_info=exc, extra={"error_type": type(exc).__name__, "error_message": str(exc)})


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
