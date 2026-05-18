"""
Request/response logging middleware.
"""
import time
import uuid

from fastapi import FastAPI, Request

from utilities.logger import get_logger, request_id_context_var

# Set up the log handler
log_handler = get_logger(__name__)


def setup_logging_middleware(app: FastAPI) -> None:
    """
    Adds request logging middleware.
    """
    @app.middleware("http")
    async def incoming_request_logger(request: Request, call_next):
        """Logs incoming requests and their response status/duration."""
        request_id = uuid.uuid4()
        request_id_context_var.set(str(request_id))

        log_handler.info(
            f"Incoming request: "
            f"\n    Method: {request.method} "
            f"\n    Url: {request.url} "
        )
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        duration_ms = round((end_time - start_time) * 1000, 2)
        log_handler.info(
            f"Completed request: "
            f"\n    Method: {request.method} "
            f"\n    Url: {request.url} "
            f"\n    Status Code: {response.status_code} "
            f"\n    Duration (ms): {duration_ms}"        
        )
        return response
