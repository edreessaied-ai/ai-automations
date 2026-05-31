"""
    This module contains transformer functions to convert
    between different data representations.
"""
from domain.ticket.models import (
    Ticket,
    TicketDraft,
    TicketIntent,
    TicketPriority,
    TicketProject,
)


def _normalize_priority(priority: str | None) -> TicketPriority:
    """
    Coerce a free-form or missing priority into a valid ticket priority,
    defaulting to "Low" when the value is absent or unrecognized.
    """
    if priority:
        normalized = priority.strip().capitalize()
        if normalized in {"Low", "Medium", "High"}:
            return TicketPriority(normalized)
    return TicketPriority.LOW


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
        priority=_normalize_priority(draft.priority),
        labels=draft.labels,
    )
