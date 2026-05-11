"""
Logger utility that writes to
~/logs/<log_name>.log.<YYYY>-<MM>-<DD>.<HH>-00

Rotates automatically when the hour changes.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from utilities.types import Json

# Cache of active loggers per timestamp
timestamp_to_logger_cache: dict[str, logging.Logger] = {}


def _get_hour_timestamp() -> str:
    """Returns timestamp rounded to the current hour."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d.%H-00")


def get_logger(
    log_name: str = "agent-lifecycle",
    level: int = logging.INFO,
    write_to_console: bool = False,
) -> logging.Logger:
    """
    Returns a logger that writes to:
    ~/logs/<log_name>.log.<YYYY>-<MM>-<DD>.<HH>-00

    Rotates automatically when the hour changes.
    """

    timestamp = _get_hour_timestamp()
    logger_key = f"{log_name}_{timestamp}"

    # Return cached logger if it exists
    if logger_key in timestamp_to_logger_cache:
        return timestamp_to_logger_cache[logger_key]

    # Resolve ~/logs directory
    log_dir = Path.home() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file path
    log_file = log_dir / f"{log_name}.log.{timestamp}"

    # Create logger
    log_handler = logging.getLogger(log_name)
    log_handler.setLevel(level)
    log_handler.propagate = False  # Prevent duplicate logs

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    log_handler.addHandler(file_handler)

    # Console handler (optional)
    if write_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        log_handler.addHandler(console_handler)

    # Cache it
    timestamp_to_logger_cache[logger_key] = log_handler

    return log_handler


def pretty_print_json(data: Json) -> str:
    """Utility to pretty print JSON data."""
    return json.dumps(data, indent=4, ensure_ascii=False)
