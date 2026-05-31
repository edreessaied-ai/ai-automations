"""
    Transforms internal domain models → Jira payloads.
"""
from typing import Any

from domain.ticket.models import TicketIntent, TicketProject
from domain.ticket.transformers import draft_to_ticket, intent_to_draft


def intent_to_jira_payload(
    ticket_intent: TicketIntent,
    project_key: TicketProject,
) -> dict[str, Any]:
    """
    Transforms a TicketIntent into a Jira API payload.
    """
    ticket_draft = intent_to_draft(ticket_intent)
    jira_ticket = draft_to_ticket(
        ticket_draft,
        ticket_project=project_key,
    )
    ticket_priority = jira_ticket.priority if jira_ticket.priority else None
    payload = {
        "fields": {
            "project": {"key": project_key},
            "issuetype": {"name": jira_ticket.type},
            "summary": jira_ticket.title or "Untitled",
            "description": jira_ticket.description or "",
            "priority": {"name": ticket_priority},
            "labels": jira_ticket.labels or [],
        }
    }
    # Remove any fields that are None to avoid Jira API errors
    payload["fields"] = {
        field: value for field, value in payload["fields"].items()
        if value is not None
    }
    return payload
