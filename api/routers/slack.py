"""
Slack router for handling Slack-related API endpoints.
"""
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

import integrations.slack.client as client
import integrations.slack.dispatcher as dispatcher
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
