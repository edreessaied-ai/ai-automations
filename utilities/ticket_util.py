"""
Ticket Utility Module
"""

import json
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from utilities.type_util import ErrStr, JSONStr

# --- Ticket Model ---


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


# --- Utility Functions ---


def parse_ticket(json_str: JSONStr) -> Ticket:
    """
    Parse raw JSON string into a validated Ticket object.
    Raises ValidationError if invalid.
    """
    data = json.loads(json_str)
    return Ticket(**data)


def try_parse_ticket(json_str: JSONStr) -> tuple[Ticket | None, ErrStr | None]:
    """
    Safe parse: returns (ticket, error)
    """
    try:
        return parse_ticket(json_str), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, str(e)


def ticket_to_json(ticket: Ticket, pretty: bool = True) -> JSONStr:
    """
    Serialize Ticket back to JSON.
    """
    if pretty:
        return ticket.model_dump_json(indent=4)
    return ticket.model_dump_json()


def ticket_to_dict(ticket: Ticket) -> dict[str, Any]:
    """
    Convert Ticket to Python dict.
    """
    return ticket.model_dump()
