"""
Main entry point for the AI Automations.
"""
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from api.middleware.cors import setup_cors
from api.middleware.exception_handler import (
    setup_exception_handler,
)
from api.middleware.logging import (
    setup_logging_middleware,
)
from api.routers.slack import slack_backend_router
from utilities.constants import BASE_DIR

# Main application entrypoint
app = FastAPI(
    title="AI Automations"
)
# Set up Jinja2 templates for rendering the Slack simulator UI
templates = Jinja2Templates(directory="templates")


# Set up middleware
setup_cors(app)
setup_logging_middleware(app)
setup_exception_handler(app)

# Resgister routers
app.include_router(slack_backend_router, prefix="/slack")


@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    """
    Render local Slack simulator UI.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/health")
def health():
    """
    Health check endpoint.
    """
    return {"status": "Healthy"}


@app.get("/favicon.ico")
def load_ui_icon_image():
    """
    Serve simulator favicon.
    """
    icon_path = (
        BASE_DIR
        / "icons"
        / "slack_bot_icon.png"
    )
    return FileResponse(icon_path)
