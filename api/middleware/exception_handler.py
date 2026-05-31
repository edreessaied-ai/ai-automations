"""
Global exception handling middleware.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from utilities.logger import get_logger

log_handler = get_logger(
    __name__,
    write_to_console=True,
)


def setup_exception_handler(app: FastAPI) -> None:
    """
    Configure global exception handler for uncaught exceptions.
    """
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Handles uncaught application exceptions.
        """
        request_body = await request.body()
        decoded_body = request_body.decode("utf-8")
        # Log the exception with request details for debugging
        log_handler.exception(
            "Unhandled exception during request processing",
            exc_info=exc,
            extra={
                "method": request.method,
                "url": str(request.url),
                "query_params": dict(request.query_params),
                "client": str(request.client) if request.client else "unknown",
                "body": decoded_body if decoded_body else "[no-body]",
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred."
            },
        )

    app.add_exception_handler(Exception, global_exception_handler)
