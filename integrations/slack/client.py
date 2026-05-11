"""
    Slack client module for Slack communications.
"""
import httpx
from fastapi.responses import JSONResponse

import integrations.slack.models as models
import utilities.exceptions as exceptions
from utilities.logger import get_logger
from utilities.types import URLStr

log_handler = get_logger(__name__)


def forward_ephemeral_acknowledgement() -> JSONResponse:
    """
    Forward an ephemeral acknowledgement response to Slack.
    """
    log_handler.info("Forwarding ephemeral acknowledgement.")
    return JSONResponse(
        content={
            "response_type": "ephemeral",
            "text": "Got it — working on your request."
        }
    )


def forward_ephemeral_error_message(error_message: str) -> JSONResponse:
    """
    Forward an ephemeral error message response to Slack.
    """
    log_handler.info(
        f"Forwarding ephemeral error message: {error_message}"
    )
    return JSONResponse(
        content={
            "response_type": "ephemeral",
            "text": f"An error occurred: {error_message}"
        }
    )


async def send_response_to_slack(
    response_url: URLStr,
    response_payload: models.SlackResponsePayload
) -> None:
    """
    Send a response back to Slack using the provided response URL.
    """
    try:
        async with httpx.AsyncClient() as async_client:
            await async_client.post(str(response_url), json=response_payload)
    except Exception as e:
        log_handler.exception("Error sending response to Slack")
        raise exceptions.SlackResponseSendError(
            f"Failed to send response to Slack: {e}"
        ) from e
