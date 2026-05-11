"""
AI Ticket Assistant - Main API Layer

This module exposes the HTTP API for generating, improving, editing,
and creating Jira tickets using AI-assisted workflows.

It is designed as a thin orchestration layer over:
- AI-based ticket generation and refinement (TicketService)
- Jira integration (JiraService)
- Stateful Slack-driven interaction (TicketContext)

Key Design Principles:
- API layer is stateless (state is passed via TicketContext)
- Business logic lives in service layer
- Endpoints represent ticket lifecycle operations
"""

# mypy: disable-error-code=misc

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from requests import Request

# from api.services.jira_service import JiraService
from api.services.ticket_service import TicketService
from domain.ticket.models import Ticket
from utilities import logger

# -------------------------
# App Initialization
# -------------------------

app = FastAPI(
    title="AI Ticket Assistant",
    description="AI-powered Slack-to-Jira ticket generation system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log_handler = logger.get_logger("ticket_api")

# -------------------------
# Domain Context
# -------------------------


class TicketContext(BaseModel):
    """
    Represents the full state of a ticket in progress.

    This object is the core of the system's state management and is used
    to support Slack-style interactive workflows where a ticket is iteratively
    refined through multiple user actions (improve, edit, create).

    Attributes:
        user_id: Identifier for the Slack user initiating the workflow.
        channel_id: Slack channel where the interaction originated.
        message_ts: Slack message timestamp used as a unique state key.
        ticket: The current state of the ticket draft.
    """

    user_id: str
    channel_id: str
    message_ts: str
    ticket: Ticket


# -------------------------
# Request Models
# -------------------------


class GenerateTicketRequest(BaseModel):
    """
    Request payload for generating a new ticket from unstructured input.

    Attributes:
        user_input: Raw text describing an issue or request.
    """

    user_input: str


class ImproveTicketRequest(BaseModel):
    """
    Request payload for improving an existing ticket draft.

    The AI will enhance clarity, completeness, and structure
    without changing the underlying intent.

    Attributes:
        context: Current ticket state.
    """

    context: TicketContext


class EditTicketRequest(BaseModel):
    """
    Request payload for modifying a ticket using natural language instructions.

    Example instruction:
        "make this high priority and mention mobile users"

    Attributes:
        context: Current ticket state.
        instruction: Natural language edit instruction.
    """

    context: TicketContext
    instruction: str


class CreateTicketRequest(BaseModel):
    """
    Request payload for creating a Jira ticket from the current draft.

    Attributes:
        context: Final ticket state to persist.
        project_key: Jira project identifier where the ticket will be created.
    """

    context: TicketContext
    project_key: str


# -------------------------
# Response Models
# -------------------------


class TicketResponse(BaseModel):
    """
    Response containing the updated ticket context after AI processing.

    This is used for iterative Slack interactions where the same
    message is updated in-place.
    """

    context: TicketContext


class CreateTicketResponse(BaseModel):
    """
    Response returned after successfully creating a Jira ticket.

    Attributes:
        jira_ticket_id: Identifier of the created Jira issue.
        jira_url: Direct link to the created ticket.
    """

    jira_ticket_id: str
    jira_url: str


# -------------------------
# Service Layer Instances
# -------------------------

ticket_service = TicketService()


async def parse_request(request: Request) -> Ticket:
    """
    Unpacks data from ticket request
    """
    ticket_request_data = await request.form()
    return ticket_request_data.get("text")


@app.post(
    "/tickets/generate",
    response_model=TicketResponse,
    summary="Generate a new ticket",
)
async def generate_ticket(request: Request) -> Ticket:
    """
    Generate a structured ticket from unstructured user input.

    This endpoint transforms raw text into a structured Ticket object
    containing title, description, priority, and labels.

    Used as the first step in the ticket lifecycle.
    """
    log_handler.info(
        "Received ticket generation request: %s", request.__dict__
    )
    ticket = Ticket(
        title="Example Ticket Title",
        description="This is an example ticket "
        "description generated from user input.",
        priority="Medium",
        labels=["example", "generated"],
    )
    return ticket


@app.post(
    "/tickets/improve",
    response_model=TicketResponse,
    summary="Improve ticket quality",
)
async def improve_ticket(req: ImproveTicketRequest) -> TicketResponse:
    """
    Improve an existing ticket draft.

    Enhances:
    - clarity
    - completeness
    - structure
    - readability

    Does not change the underlying intent of the ticket.
    """

    updated_ticket = ticket_service.improve(req.context.ticket)
    req.context.ticket = updated_ticket

    return TicketResponse(context=req.context)


@app.post(
    "/tickets/edit",
    response_model=TicketResponse,
    summary="Edit ticket using natural language",
)
async def edit_ticket(req: EditTicketRequest) -> TicketResponse:
    """
    Modify a ticket based on a natural language instruction.

    This allows users to apply targeted changes such as:
    - changing priority
    - adding context
    - refining scope
    """

    updated_ticket = ticket_service.edit(
        req.context.ticket,
        req.instruction,
    )

    req.context.ticket = updated_ticket

    return TicketResponse(context=req.context)
