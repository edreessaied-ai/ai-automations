"""
    Slack client module for Slack communications.
"""
import httpx

import integrations.slack.models as models
from utilities.types import URLStr


async def send_response_to_slack(
    response_url: URLStr,
    response_payload: models.SlackResponsePayload
) -> None:
    """
    Send a response back to Slack using the provided response URL.
    """
    async with httpx.AsyncClient() as async_client:
        await async_client.post(response_url, json=response_payload)
