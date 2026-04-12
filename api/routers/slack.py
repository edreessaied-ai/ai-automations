"""
Slack router for handling Slack-related API endpoints.
"""
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.routers.ticket import (
    GenerateTicketRequest,
    ImproveTicketRequest,
    TicketContext,
    TicketResponse,
    generate_ticket,
    improve_ticket,
)

slack_router = APIRouter(prefix="/slack", tags=["slack"])


# -------------------------
# Slack Event Models
# -------------------------

class SlackEvent(BaseModel):
    """
    Model for Slack Events API payloads (simplified for message events).
    """
    user: str | None = None
    text: str | None = None


class SlackCommand(BaseModel):
    text: str
    user_id: str


# -------------------------
# Helpers
# -------------------------

def build_context(user_id: str, channel_id: str, message_ts: str, ticket):
    """
    Build a TicketContext from Slack event data.
    """
    return TicketContext(
        user_id=user_id,
        channel_id=channel_id,
        message_ts=message_ts,
        ticket=ticket,
    )


# -------------------------
# Slack Event Endpoint
# -------------------------

@slack_router.post("/events")
async def slack_events(payload: SlackEvent):
    """
    Handle Slack Events API (message events, etc.)
    """

    if payload.type != "message" or not payload.text:
        return {"ok": True}

    # Example trigger: simple keyword
    if "ticket" in payload.text.lower():
        req = GenerateTicketRequest(user_input=payload.text)

        result: TicketResponse = await generate_ticket(req)

        return {
            "ok": True,
            "message": "Ticket generated",
            "context": result.context.model_dump(),
        }

    return {"ok": True}


# -------------------------
# Slack Slash Command
# -------------------------

@slack_router.post("/commands")
async def slack_commands(cmd: SlackCommand):
    """
    Handle Slack slash commands like /ticket
    """

    text = cmd.text.strip()

    if cmd.command == "/ticket":
        req = GenerateTicketRequest(user_input=text)

        result: TicketResponse = await generate_ticket(req)

        return {
            "response_type": "in_channel",
            "text": "🧾 Ticket generated",
            "ticket": result.context.ticket.model_dump(),
        }

    if cmd.command == "/ticket-improve":
        # minimal context example (you’ll likely hydrate from DB later)
        context = build_context(
            user_id=cmd.user_id,
            channel_id=cmd.channel_id,
            message_ts=cmd.response_url,  # placeholder
            ticket=None,  # replace with stored ticket later
        )

        req = ImproveTicketRequest(context=context)
        result = await improve_ticket(req)

        return {
            "response_type": "ephemeral",
            "text": "✨ Ticket improved",
            "ticket": result.context.ticket.model_dump(),
        }

    raise HTTPException(status_code=400, detail="Unknown Slack command")


# -------------------------
# Slack Action Endpoint (future use)
# -------------------------

@slack_router.post("/actions")
async def slack_actions(request: Request):
    """
    Handle interactive Slack components (buttons, modals, etc.)
    """
    payload = await request.form()

    # Slack sends JSON inside "payload"
    data = json.loads(payload.get("payload", "{}"))

    return {
        "ok": True,
        "type": data.get("type"),
    }
