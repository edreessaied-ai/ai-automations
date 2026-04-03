"""
Test suite for Ticket model validation and parsing logic.
"""
import pytest
from pydantic import ValidationError

from utilities.ticket_util import Ticket


# ----------------------------
# AI-like inputs
# ----------------------------

VALID_AI_OUTPUT = {
    "title": "Login bug",
    "description": "Login fails when submitting form",
    "priority": "High",
    "labels": ["bug", "auth"]
}

MINIMAL_VALID_OUTPUT = {
    "title": "Bug",
    "description": "Something broke",
    "priority": "Low",
    "labels": []
}

INVALID_PRIORITY_OUTPUT = {
    "title": "Bug",
    "description": "Crash",
    "priority": "URGENT",
    "labels": ["bug"]
}

MISSING_FIELDS_OUTPUT = {
    "title": "Bug"
}

EXTRA_FIELDS_OUTPUT = {
    "title": "Bug",
    "description": "Crash",
    "priority": "High",
    "labels": [],
    "confidence": 0.99,
}

WRONG_TYPE_OUTPUT = {
    "title": 123,
    "description": "Crash",
    "priority": "High",
    "labels": ["bug"]
}

LABELS_WRONG_TYPE_OUTPUT = {
    "title": "Bug",
    "description": "Crash",
    "priority": "High",
    "labels": "bug,auth"
}


# ----------------------------
# Happy path tests
# ----------------------------

def test_valid_ai_output():
    """Ensures valid AI output is correctly parsed into a Ticket model."""
    ticket = Ticket.model_validate(VALID_AI_OUTPUT)

    assert ticket.title == "Login bug"
    assert ticket.priority == "High"
    assert isinstance(ticket.labels, list)


def test_minimal_valid_output():
    """Ensures minimal valid input still produces a valid Ticket."""
    ticket = Ticket.model_validate(MINIMAL_VALID_OUTPUT)

    assert ticket.priority == "Low"
    assert ticket.labels == []


# ----------------------------
# Schema enforcement tests
# ----------------------------

def test_missing_required_fields():
    """Ensures missing required fields raise a validation error."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(MISSING_FIELDS_OUTPUT)


def test_extra_fields_rejected():
    """Ensures unexpected extra fields are rejected by strict schema rules."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(EXTRA_FIELDS_OUTPUT)


# ----------------------------
# Type safety tests
# ----------------------------

def test_wrong_type_title():
    """
    Ensures incorrect field types (e.g., int
    instead of str) are rejected.
    """
    with pytest.raises(ValidationError):
        Ticket.model_validate(WRONG_TYPE_OUTPUT)


def test_wrong_type_labels():
    """Ensures labels field must be a list of strings."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(LABELS_WRONG_TYPE_OUTPUT)


# ----------------------------
# Business rule validation
# ----------------------------

def test_invalid_priority_rejected():
    """
    Ensures invalid priority values are rejected by
    custom validation rules.
    """
    with pytest.raises(ValidationError):
        Ticket.model_validate(INVALID_PRIORITY_OUTPUT)


# ----------------------------
# AI robustness tests
# ----------------------------

def test_ai_adds_unknown_fields_does_not_silently_pass():
    """
    Ensures AI-generated unknown fields
    cause validation failure under strict schema.
    """
    bad_ai_output = {
        **VALID_AI_OUTPUT,
        "random_field": "should not exist"
    }

    with pytest.raises(ValidationError):
        Ticket.model_validate(bad_ai_output)


def test_ai_partial_output_fails_cleanly():
    """
    Ensures incomplete AI outputs are rejected
    when required fields are missing.
    """
    partial = {
        "title": "Bug reported",
        "priority": "High"
    }

    with pytest.raises(ValidationError):
        Ticket.model_validate(partial)


# ----------------------------
# Regression / stability test
# ----------------------------

def test_ticket_schema_is_stable_snapshot():
    """
    Ensures the Ticket JSON schema contains expected
    fields and forbids extras.
    """
    schema = Ticket.model_json_schema()

    assert "title" in schema["properties"]
    assert "description" in schema["properties"]
    assert "priority" in schema["properties"]
    assert "labels" in schema["properties"]
    assert schema["additionalProperties"] is False
