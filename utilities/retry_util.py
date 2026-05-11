"""
Simple Retry Utility

Provides a straightforward retry mechanism for retrying function calls
with a fixed interval between attempts.
"""

import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from utilities import logger

T = TypeVar("T")
P = ParamSpec("P")

log_handler = logger.get_logger()


class RetryException(Exception):
    """
    Custom exception for retry failures,
    used when retries have been exhausted.
    """


def retry(
    func: Callable[..., T],
    *args: Any,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    retry_max_retries: int = 3,
    retry_interval: float = 1.0,
    **kwargs: Any,
) -> T:
    """
    Retry a function call with a fixed interval between attempts.
    """
    exc_str = ""
    for attempt in range(retry_max_retries + 1):
        try:
            return func(*args, **kwargs)
        except retry_exceptions as exc:
            if attempt == retry_max_retries:
                break

            exc_str = str(exc)
            log_handler.info(
                f"Retrying due to exception: {exc_str}. "
                f"Retries left: {retry_max_retries - attempt}",
            )
            time.sleep(retry_interval)
    raise RetryException(
        f"Failed after {retry_max_retries} retries, last exception: {exc_str}"
    )
