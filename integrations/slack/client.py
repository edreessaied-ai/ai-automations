"""
    Slack client module for Slack communications.
"""
import os
from typing import Any

import httpx
from fastapi.responses import JSONResponse

import integrations.slack.local_store as local_store
import integrations.slack.models as models
import utilities.exceptions as exceptions
from utilities.logger import get_logger
from utilities.types import URLStr

log_handler = get_logger(__name__)

# Slack Web API base. Methods are appended (e.g. ".../conversations.replies").
SLACK_API_BASE_URL = "https://slack.com/api"
SLACK_API_TIMEOUT = 15  # seconds


def _bot_token() -> str | None:
    """
    Return the configured Slack bot token, or None when running locally.

    When absent, the client transparently falls back to the in-memory
    `local_store` so the full flow stays demoable without a workspace.
    """
    return os.getenv("SLACK_BOT_TOKEN")


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


def _parse_thread_messages(
    messages: list[dict[str, Any]],
) -> list[models.SlackThreadMessage]:
    """
    Convert raw `conversations.replies` messages into thread messages,
    preserving chronological order (Slack already returns them oldest-first).
    """
    parsed: list[models.SlackThreadMessage] = []
    for message in messages:
        text = str(message.get("text") or "").strip()
        if not text:
            continue
        parsed.append(
            models.SlackThreadMessage(
                # `user` for human messages, `bot_id` for bot/app messages.
                user=str(message.get("user") or message.get("bot_id") or ""),
                text=text,
                timestamp=str(message.get("ts") or ""),
            )
        )
    return parsed


async def fetch_thread_replies(
    channel_id: str,
    thread_ts: str,
) -> models.SlackThreadContext:
    """
    Retrieve a thread's parent message and replies via `conversations.replies`.

    Falls back to the local store (simulator) when no bot token is configured.
    """
    token = _bot_token()
    if not token:
        seeded = local_store.get_seeded_thread(channel_id, thread_ts)
        if seeded is None:
            raise exceptions.SlackThreadContextError(
                "No thread context available for "
                f"channel={channel_id} thread_ts={thread_ts}."
            )
        return seeded

    try:
        async with httpx.AsyncClient() as async_client:
            response = await async_client.get(
                f"{SLACK_API_BASE_URL}/conversations.replies",
                headers={"Authorization": f"Bearer {token}"},
                params={"channel": channel_id, "ts": thread_ts},
                timeout=SLACK_API_TIMEOUT,
            )
        data = response.json()
    except Exception as e:
        log_handler.exception("Error fetching Slack thread replies")
        raise exceptions.SlackThreadContextError(
            f"Failed to fetch Slack thread: {e}"
        ) from e

    if not data.get("ok"):
        raise exceptions.SlackThreadContextError(
            f"Slack conversations.replies failed: {data.get('error')}"
        )

    messages = _parse_thread_messages(data.get("messages", []))
    if not messages:
        raise exceptions.SlackThreadContextError(
            "Slack thread contained no usable messages."
        )
    return models.SlackThreadContext(
        channel_id=channel_id,
        thread_ts=thread_ts,
        messages=messages,
    )


async def post_message(
    channel_id: str,
    thread_ts: str,
    message: models.SlackMessage,
) -> None:
    """
    Post a message into a thread via `chat.postMessage`.

    Falls back to the local store (simulator) when no bot token is configured.
    """
    payload = message.to_slack_response()
    token = _bot_token()
    if not token:
        local_store.publish_message(dict(payload))
        return

    body: dict[str, Any] = {
        "channel": channel_id,
        "thread_ts": thread_ts,
        **payload,
    }
    try:
        async with httpx.AsyncClient() as async_client:
            response = await async_client.post(
                f"{SLACK_API_BASE_URL}/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
                timeout=SLACK_API_TIMEOUT,
            )
        data = response.json()
    except Exception as e:
        log_handler.exception("Error posting message to Slack")
        raise exceptions.SlackResponseSendError(
            f"Failed to post message to Slack: {e}"
        ) from e

    if not data.get("ok"):
        raise exceptions.SlackResponseSendError(
            f"Slack chat.postMessage failed: {data.get('error')}"
        )
