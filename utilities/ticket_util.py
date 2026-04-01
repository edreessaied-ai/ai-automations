"""
    Ticket Utility Module
"""
import json

from typing import List
from pydantic import BaseModel, Field, ValidationError, field_validator


# --- Ticket Model ---

class Ticket(BaseModel):
    """
        Represents a structured Jira ticket
    """
    title: str = Field(
        ...,
        description="Short summary of the issue"
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the issue"
    )
    priority: str = Field(
        ...,
        description="Priority level: Low, Medium, High"
    )
    labels: List[str] = Field(
        ...,
        description="List of tags for categorization"
    )

    # --- Enforce enum manually (matches JSON schema) ---
    @classmethod
    @field_validator("priority")
    def validate_priority(cls, v: str) -> str:
        """
            Validate that priority is one of the allowed values.
        """
        allowed = {"Low", "Medium", "High"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v

    class Config:
        """
            Pydantic configuration to match JSON schema constraints.
        """
        extra = "forbid"  # matches "additionalProperties": False


# --- Utility Functions ---

def parse_ticket(json_str: str) -> Ticket:
    """
    Parse raw JSON string into a validated Ticket object.
    Raises ValidationError if invalid.
    """
    data = json.loads(json_str)
    return Ticket(**data)


def try_parse_ticket(json_str: str):
    """
    Safe parse: returns (ticket, error)
    """
    try:
        return parse_ticket(json_str), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, str(e)


def ticket_to_json(ticket: Ticket, pretty: bool = True) -> str:
    """
    Serialize Ticket back to JSON.
    """
    if pretty:
        return ticket.model_dump_json(indent=4)
    return ticket.model_dump_json()


def ticket_to_dict(ticket: Ticket) -> dict:
    """
    Convert Ticket to Python dict.
    """
    return ticket.model_dump()
