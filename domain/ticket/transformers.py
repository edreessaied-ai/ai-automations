"""
    This module contains transformer functions to convert
    between different data representations.
"""
from domain.ticket.models import (
    Ticket,
    TicketDraft,
    TicketIntent,
    TicketProject,
)


def intent_to_draft(intent: TicketIntent) -> TicketDraft:
    """
    Transforms a TicketIntent into a TicketDraft,
    allowing for optional fields to be left as None.
    """
    return TicketDraft(
        title=intent.title,
        description=intent.description,
        priority=intent.priority,
        assignee=intent.assignee,
        labels=intent.labels or [],
    )


def draft_to_ticket(
    draft: TicketDraft,
    ticket_project: TicketProject
) -> Ticket:
    """
    Transforms a TicketDraft into a Ticket, applying default values
    for any missing fields.
    """
    return Ticket(
        ticket_project=ticket_project,
        title=draft.title or "Untitled",
        type="Task",
        impact="Medium",
        description=draft.description or "",
        priority=draft.priority,
        labels=draft.labels,
    )
