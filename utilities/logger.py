"""
Centralized logging utility with hourly log rotation.

Log files are written to:

~/logs/<log_name>.log

and automatically rotated every hour into files like:

<log_name>.log.2026-05-19_18

Features:
- Hourly log rotation
- Automatic flushing after each record
- Request-scoped request_id injection
- Optional console logging
- Duplicate-handler protection
- Safe singleton logger configuration
"""

import json
import logging
from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from utilities.types import Json

request_id_context_var: ContextVar[str] = ContextVar(
    "request_id",
    default="no-active-request"
)


class RequestContextFilter(logging.Filter):
    """Inject request_id from contextvars into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context_var.get()
        return True


class FlushTimedRotatingFileHandler(
    TimedRotatingFileHandler
):
    """
    Timed rotating file handler that flushes
    immediately after each log record.
    """

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


class FlushStreamHandler(logging.StreamHandler):
    """
    Stream handler that flushes immediately
    after each log record.
    """

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def get_logger(
    log_name: str = "agent-lifecycle",
    level: int = logging.INFO,
    write_to_console: bool = False,
) -> logging.Logger:
    """
    Returns a configured singleton logger.

    Logs rotate automatically every hour.
    """

    logger = logging.getLogger(log_name)

    # Prevent duplicate configuration
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Create ~/logs directory
    log_dir = Path.home() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Base log file path
    log_file = log_dir / f"{log_name}.log"

    # Shared formatter
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(request_id)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    context_filter = RequestContextFilter()

    # Rotating file handler
    file_handler = FlushTimedRotatingFileHandler(
        filename=log_file,
        when="H",
        interval=1,
        backupCount=168,  # Keep 7 days of hourly logs
        encoding="utf-8",
    )

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    logger.addHandler(file_handler)

    # Optional console handler
    if write_to_console:
        console_handler = FlushStreamHandler()

        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(context_filter)

        logger.addHandler(console_handler)

    return logger


def pretty_print_json(data: Json) -> str:
    """Pretty-print JSON data."""

    return json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
    )
