"""
Ticket Models - Defines the data structures for representing tickets.
"""
from typing import Any, Literal

from pydantic import BaseModel


class TicketIntent(BaseModel):
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
        lines = [
            f"Received ticket request: {self.title}",
            "Here's the ticket intent:",
            ""
        ]
        if self.description:
            lines.append(f" Description: {self.description}")
        if self.priority:
            lines.append(f" Priority: {self.priority.capitalize()}")
        if self.assignee:
            lines.append(f" Assignee: {self.assignee}")
        if self.labels:
            lines.append(f" Labels: {', '.join(self.labels)}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the TicketIntent to a dictionary.
        """
        return self.model_dump()


class TicketDraft(BaseModel):
    """
    Represents a draft version of a ticket, which may have optional fields
    """
    title: str | None
    description: str | None
    priority: str | None
    assignee: str | None
    labels: list[str] = []


class Ticket(BaseModel):
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

    class Config:  # pylint: disable=too-few-public-methods
        """
        Pydantic configuration to match JSON schema constraints.

        - `extra = "forbid"` ensures that any additional fields
        not defined in the model will cause validation to fail,
        enforcing a strict schema.
        """

        extra = "forbid"


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
