"""
Slack router for handling Slack-related API endpoints.
"""
import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

import integrations.slack.client as client
import integrations.slack.dispatcher as dispatcher
import integrations.slack.local_store as local_store
import integrations.slack.models as models
import integrations.slack.parser as parser
from utilities.logger import get_logger

# Set up logger for this module
log_handler = get_logger(__name__)
# API router for slack-related endpoints
slack_backend_router = APIRouter()
# Set up Jinja2 templates for rendering the Slack simulator UI
templates = Jinja2Templates(directory="templates")
# Shared in-memory state
latest_slack_response: dict[str, Any] = {}


@slack_backend_router.post("/commands")
async def slack_command_router(
    request: Request,
    background_tasks_manager: BackgroundTasks
) -> JSONResponse:
    """
    Endpoint to receive Slack slash commands.
    """
    slack_payload = await request.form()
    slack_command_request = (
        parser.build_slack_command_request(
            dict(slack_payload)
        )
    )
    background_tasks_manager.add_task(
        dispatcher.slack_intent_handler,
        slack_command_request
    )
    return client.forward_ephemeral_acknowledgement()


@slack_backend_router.post("/events")
async def slack_events_router(
    request: Request,
    background_tasks_manager: BackgroundTasks,
) -> JSONResponse:
    """
    Slack Events API endpoint.

    Handles the one-time URL verification handshake and `app_mention` events.
    Real Slack requires a fast acknowledgement, so the actual work (thread
    retrieval, LLM generation, posting the draft) runs in the background.
    """
    payload: dict[str, Any] = await request.json()

    # Slack URL verification handshake.
    if payload.get("type") == "url_verification":
        return JSONResponse(content={"challenge": payload.get("challenge")})

    event = payload.get("event", {})
    if payload.get("type") == "event_callback" and (
        event.get("type") == "app_mention"
    ):
        app_mention = parser.parse_app_mention_event(event)
        background_tasks_manager.add_task(
            dispatcher.handle_app_mention, app_mention
        )

    # Acknowledge immediately so Slack does not retry.
    return JSONResponse(content={"ok": True})


@slack_backend_router.post("/interactions")
async def slack_interactions_router(
    request: Request,
    background_tasks_manager: BackgroundTasks,
) -> JSONResponse:
    """
    Slack interactivity endpoint for the draft confirmation buttons.

    Slack posts an `application/x-www-form-urlencoded` body with a JSON
    `payload` field; the local simulator posts JSON directly.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        raw_payload: dict[str, Any] = await request.json()
    else:
        form = await request.form()
        raw_payload = json.loads(str(form.get("payload") or "{}"))

    interaction = parser.parse_interaction_payload(raw_payload)
    background_tasks_manager.add_task(
        dispatcher.handle_interaction, interaction
    )
    return JSONResponse(content={"ok": True})


@slack_backend_router.post("/sim/thread")
def seed_simulated_thread(
    thread_context: models.SlackThreadContext,
) -> JSONResponse:
    """
    Local-simulator helper: seed a thread so the bot can "read" it without a
    real Slack workspace. Stands in for `conversations.replies`.
    """
    local_store.seed_thread(thread_context)
    log_handler.info(
        f"Seeded simulated thread {thread_context.thread_ts} with "
        f"{len(thread_context.messages)} message(s)."
    )
    return JSONResponse(content={"ok": True})


@slack_backend_router.get("/sim/latest-message")
def get_latest_simulated_message() -> JSONResponse:
    """
    Local-simulator helper: return the most recent message the bot "posted".
    """
    return JSONResponse(content=local_store.get_latest_message())


@slack_backend_router.get("/responses")
def get_latest_slack_response() -> JSONResponse:
    """
    Endpoint to retrieve the latest Slack response for testing purposes.
    """
    return JSONResponse(content=latest_slack_response)


@slack_backend_router.post("/responses")
def receive_slack_response(slack_response: dict[str, Any]) -> JSONResponse:
    """
    Endpoint to receive Slack responses from
    the dispatcher for testing purposes.
    """
    latest_slack_response.update(slack_response)
    log_handler.info(
        f"Received Slack response: {latest_slack_response}"
    )
    return JSONResponse(content={"detail": "Slack response received."})
