"""
Main API for the AI Automations project.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.frontdesk_agent import run_agent
from agents.ticket_agent import (
    edit_ticket,
    generate_ticket,
    improve_ticket,
)
from utilities.ticket_util import Ticket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 👈 important
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.
    """

    message: str


class GenerateTicketRequest(BaseModel):
    """
    Request model for generating a ticket.
    """

    user_input: str


class ImproveTicketRequest(BaseModel):
    """
    Request model for improving a ticket.
    """

    ticket: Ticket


class EditTicketRequest(BaseModel):
    """
    Request model for editing a ticket.
    """

    ticket: Ticket
    instruction: str


@app.post("/chat")  # type: ignore[misc]
async def chat(req: ChatRequest) -> str:
    """
    Chat endpoint that takes user message,
    and returns AI-generated message.
    """
    result = await run_agent(req.message)

    message = result.get("message")
    if not isinstance(message, str):
        raise ValueError("Invalid response from agent")

    return message


@app.post("/tickets/generate")  # type: ignore[misc]
async def api_generate_ticket(req: GenerateTicketRequest) -> Ticket:
    """
    Generate a new ticket from user input.
    """
    return generate_ticket(req.user_input)


@app.post("/tickets/improve")  # type: ignore[misc]
async def api_improve_ticket(req: ImproveTicketRequest) -> Ticket:
    """
    Improve an existing ticket by enhancing clarity,
    structure, and completeness.
    """
    return improve_ticket(req.ticket)


@app.post("/tickets/edit")  # type: ignore[misc]
async def api_edit_ticket(req: EditTicketRequest) -> Ticket:
    """
    Modify a ticket based on a natural language instruction.
    """
    return edit_ticket(req.ticket, req.instruction)


@app.get("/")  # type: ignore[misc]
def root() -> dict[str, str]:
    """
    Root endpoint.
    """
    return {"message": "API is running"}
