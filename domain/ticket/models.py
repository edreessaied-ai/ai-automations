"""
Ticket Models - Defines the data structures for representing tickets.
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# Alias Types
TicketUserPromptText = str


# Pydantic Models for Ticket Data
class StrictBaseModel(BaseModel):
    """
    Pydantic model with strict validation to ensure
    that only well-formed data is accepted.
    """
    model_config = ConfigDict(extra="forbid")


class TicketIntent(StrictBaseModel):
    """
    Represents the intent of a ticket-related action,
    such as creating or improving a ticket.
    """
    title: str | None
    description: str | None
    priority: str | None
    assignee: str | None
    labels: list[str] | None

    def to_string(self) -> str:
        """
        Returns a string representation of the TicketIntent.
        """
        lines = ["Ticket Intent:"]
        if self.title:
            lines.append(f"     Title: {self.title}")
        if self.description:
            lines.append(f"     Description: {self.description}")
        if self.priority:
            lines.append(f"     Priority: {self.priority.capitalize()}")
        if self.assignee:
            lines.append(f"     Assignee: {self.assignee}")
        if self.labels:
            lines.append(f"     Labels: {', '.join(self.labels)}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the TicketIntent to a dictionary.
        """
        return self.model_dump()


class TicketDraft(StrictBaseModel):
    """
    Represents a draft version of a ticket, which may have optional fields
    """
    title: str | None
    description: str | None
    priority: str | None
    assignee: str | None
    labels: list[str] = []


class Ticket(StrictBaseModel):
    """
    Uses pydantic model to represent a structured Jira ticket

    Pydantic models are used here to provide a strict validation boundary
    for untrusted input (e.g., AI-generated data).

    They enforce schema correctness, perform type coercion,
    and fail fast with clear errors when data is invalid.

    This ensures only well-formed, reliable ticket data enters the system,
    reducing bugs, simplifying parsing, and improving debuggability in
    production pipelines.
    """

    title: str
    type: str
    impact: str
    description: str
    priority: Literal["Low", "Medium", "High"]
    labels: list[str]


def pretty_print_ticket(ticket: Ticket) -> str:
    """
    Utility to pretty print a Ticket object.
    """
    return (
        "\n\n"
        f"Title: \n{ticket.title}\n\n"
        f"Priority: \n{ticket.priority}\n\n"
        f"Labels: \n{', '.join(ticket.labels)}\n\n"
        f"Description:\n{ticket.description}"
    )


def format_ticket_intent(intent: TicketIntent) -> str:
    """
    Formats a TicketIntent into a human-readable string.
    """
    sections = ["🎫 *Received Ticket Request*"]

    if intent.title:
        sections.append(f"*Title:*\n{intent.title}")

    if intent.description:
        sections.append(f"*Description:*\n{intent.description}")

    if intent.priority:
        sections.append(f"*Priority:* {intent.priority}")

    if intent.assignee:
        sections.append(f"*Assignee:* {intent.assignee}")

    if intent.labels:
        sections.append(f"*Labels:* {', '.join(intent.labels)}")

    if len(sections) == 1:
        sections.append("_No structured details detected._")

    # 👇 Add confirmation prompt
    sections.append(
        "_Does this look correct?_ \n"
        "Reply with *yes* to confirm or tell me what to change."
    )

    return "\n\n".join(sections)
