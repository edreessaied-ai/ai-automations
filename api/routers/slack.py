"""
Slack router for handling Slack-related API endpoints.
"""
from collections.abc import Callable

import httpx
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import integrations.slack.models as slack_models
from domain.ticket.pipeline import send_ticket_request_to_llm
from utilities.exceptions import SlackUnknownCommandError
from utilities.logger import get_logger
from utilities.types import (
    URLStr,
)

logger = get_logger(__name__)

slack_router = APIRouter(prefix="/slack", tags=["slack"])

# Application instance
app = FastAPI(title="AI Automations Slack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

slack_command_names = [e.value for e in slack_models.SlackRequestType]

def normalize_slack_command(slack_command_str: str) -> str:
    """
    Normalize the incoming Slack command by
    stripping leading/trailing slash
    """
    return slack_command_str.lstrip("/")


def build_slack_command_request(
    payload: slack_models.UnnormalizedSlackRequest
) -> slack_models.NormalizedSlackCommandRequest:
    """
    Convert raw Slack payload → internal request model.
    """
    command = payload.get("command")
    normalized_command = normalize_slack_command(command)
    return slack_models.NormalizedSlackCommandRequest(
        intent=normalized_command,
        text=payload.get("text"),
        user_id=payload.get("user_id"),
        channel_id=payload.get("channel_id"),
        response_url=payload.get("response_url"),
        thread_ts=payload.get("thread_ts"),
    )


async def send_response_to_slack(
    response_url: URLStr,
    payload: slack_models.SlackResponsePayload
) -> None:
    """
    Send a response back to Slack using the provided response URL.
    """
    async with httpx.AsyncClient() as client:
        await client.post(response_url, json=payload)


async def slack_intent_handler(
    slack_command_request: slack_models.NormalizedSlackCommandRequest
) -> None:
    """
    Handler for routing Slack commands to the appropriate function.
    """
    request_handler = slack_intent_to_api_handler.get(
        slack_command_request.intent
    )
    if not request_handler:
        raise SlackUnknownCommandError(
            f"No handler defined for command: "
            f"{slack_command_request.intent}"
        )
    slack_response = await request_handler(slack_command_request)
    await send_response_to_slack(
        slack_command_request.response_url,
        slack_response
    )


async def ticket_creation_handler(
    slack_command_request: slack_models.NormalizedSlackCommandRequest
) -> slack_models.SlackResponsePayload:
    """
    Handler for ticket-related Slack commands.
    """
    ticket_intent = send_ticket_request_to_llm(
        user_prompt=slack_command_request.text,
    )
    logger.info(ticket_intent)
    # Build a Slack message with the ticket intent
    # and return it as a Slack response
    slack_message = slack_models.SlackMessage(
        text=ticket_intent.to_string(),
    )
    return slack_message.to_slack_response()


# Map of Slack intents to their corresponding API handlers
slack_intent_to_api_handler: dict[
    slack_models.SlackRequestType,
    Callable[
        [slack_models.NormalizedSlackCommandRequest],
        slack_models.SlackResponsePayload]
    ] = {
        slack_models.SlackRequestType.CREATE_TICKET: ticket_creation_handler
    }

@app.post("/slack/commands")
async def slack_commands(
    request: Request,
    background_tasks_manager: BackgroundTasks
) -> JSONResponse:
    """
    Endpoint to receive Slack slash commands.
    """
    slack_payload = await request.form()
    try:
        # Handle the Slack command
        slack_command_request = build_slack_command_request(
            slack_payload
        )
        # Add the command handler to background tasks
        # so that we can respond to Slack immediately
        background_tasks_manager.add_task(
            slack_intent_handler,
            slack_command_request
        )
        # Immediate acknowledgement to Slack
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": "Got it — working on your request."
            }
        )
    except SlackUnknownCommandError as e:
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text":
                    f"Error: {str(e)}; please use one of the "
                    f"following commands: "
                    f"{', '.join(slack_command_names)}",
            }
        )
