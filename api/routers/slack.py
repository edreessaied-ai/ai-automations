"""
Slack router for handling Slack-related API endpoints.
"""
import os

from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import integrations.slack.dispatcher as dispatcher
import integrations.slack.models as models
import integrations.slack.parser as parser
from utilities.logger import get_logger

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

slack_command_names = [e.value for e in models.SlackRequestType]

templates = Jinja2Templates(directory="templates")


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
        slack_command_request = parser.build_slack_command_request(
            slack_payload
        )
        # Add the command handler to background tasks
        # so that we can respond to Slack immediately
        background_tasks_manager.add_task(
            dispatcher.slack_intent_handler,
            slack_command_request
        )
        # Immediate acknowledgement to Slack
        ephemeral_response = {
            "response_type": "ephemeral",
            "text": "Got it — working on your request."
        }
        logger.info(
            f"Received Slack command: "
            f"{slack_command_request.intent}; "
            f"Returning ephemeral acknowledgement to Slack "
            f"the command is being processed in the background: "
            f"{ephemeral_response}"
        )
        return JSONResponse(ephemeral_response)
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error processing Slack command: {e}")
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": f"An error occurred while "
                f"processing your request: {e}",
            }
        )


@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    """
    Simple home page to verify that the API is running.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
    )


@app.get("/favicon.ico")
def favicon():
    """
    Serve the favicon for the API documentation and home page.
    """
    path = os.path.expanduser("~/code/ai-automations/icons/slack_bot_icon.png")
    return FileResponse(path)
