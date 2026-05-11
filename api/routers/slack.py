"""
Slack router for handling Slack-related API endpoints.
"""
import json
import os

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import integrations.slack.client as client
import integrations.slack.dispatcher as dispatcher
import integrations.slack.parser as parser
from utilities.logger import get_logger

log_handler = get_logger(__name__)

app = FastAPI(title="AI Automations Slack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Shared in-memory state
latest_slack_response = {}


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
        log_handler.info(
            "Received Slack payload: %s",
            dict(slack_payload)
        )

        slack_command_request = (
            parser.build_slack_command_request(
                slack_payload
            )
        )

        log_handler.info(
            "Built Slack command request: %s",
            slack_command_request
        )

        background_tasks_manager.add_task(
            dispatcher.slack_intent_handler,
            slack_command_request
        )

        return client.forward_ephemeral_acknowledgement()

    except Exception as error:  # pylint: disable=broad-except
        log_handler.exception(
            "Error processing Slack command"
        )

        return client.forward_ephemeral_error_message(
            str(error)
        )


@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    """
    Render local Slack simulator UI.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/favicon.ico")
def favicon():
    """
    Serve favicon.
    """
    path = os.path.expanduser(
        "~/code/ai-automations/icons/slack_bot_icon.png"
    )

    return FileResponse(path)


@app.post("/slack-responses")
async def receive_response(
    request: Request
) -> JSONResponse:
    """
    Receive async Slack-style response
    (simulated response_url webhook).

    Stores ONLY the latest response.
    """
    log_handler.info(
        "POST /slack-responses received"
    )

    client_response = await request.json()

    latest_slack_response.clear()
    latest_slack_response.update(client_response)

    log_handler.info(
        "Stored latest Slack response:\n%s",
        json.dumps(
            latest_slack_response,
            indent=2
        )
    )

    return JSONResponse(
        content={
            "status": "ok",
            "stored_response": latest_slack_response
        }
    )


@app.get("/slack-responses")
async def get_response() -> JSONResponse:
    """
    Return latest async Slack response.
    """
    log_handler.info(
        "GET /slack-responses returning:\n%s",
        json.dumps(
            latest_slack_response,
            indent=2
        )
    )
    return JSONResponse(
        content=latest_slack_response
    )
