"""
Comprehensive test suite for Ticket model:
- schema validation
- AI robustness
- edge cases
- coercion behavior
- serialization stability
"""

import pytest
from pydantic import ValidationError
from utilities.ticket_util import Ticket

# ----------------------------
# Base valid inputs
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

# ----------------------------
# Invalid inputs
# ----------------------------

INVALID_PRIORITY_OUTPUT = {
    "title": "Bug",
    "description": "Crash",
    "priority": "URGENT",
    "labels": ["bug"]
}

MISSING_FIELDS_OUTPUT = {
    "title": "Bug"
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


# =========================================================
# HAPPY PATH
# =========================================================

def test_valid_ai_output():
    ticket = Ticket.model_validate(VALID_AI_OUTPUT)
    assert ticket.title == "Login bug"
    assert ticket.priority == "High"
    assert isinstance(ticket.labels, list)


def test_minimal_valid_output():
    ticket = Ticket.model_validate(MINIMAL_VALID_OUTPUT)
    assert ticket.priority == "Low"
    assert ticket.labels == []


# =========================================================
# SCHEMA ENFORCEMENT
# =========================================================

def test_missing_required_fields():
    with pytest.raises(ValidationError):
        Ticket.model_validate(MISSING_FIELDS_OUTPUT)


def test_extra_fields_rejected():
    bad = {
        **VALID_AI_OUTPUT,
        "confidence": 0.99
    }
    with pytest.raises(ValidationError):
        Ticket.model_validate(bad)


def test_unknown_field_rejected():
    bad = {
        **VALID_AI_OUTPUT,
        "random_field": "not allowed"
    }
    with pytest.raises(ValidationError):
        Ticket.model_validate(bad)


# =========================================================
# TYPE SAFETY
# =========================================================

def test_wrong_type_title():
    with pytest.raises(ValidationError):
        Ticket.model_validate(WRONG_TYPE_OUTPUT)


def test_wrong_type_labels():
    with pytest.raises(ValidationError):
        Ticket.model_validate(LABELS_WRONG_TYPE_OUTPUT)


# =========================================================
# BUSINESS RULES
# =========================================================

def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        Ticket.model_validate(INVALID_PRIORITY_OUTPUT)


# =========================================================
# EDGE CASES (IMPORTANT FOR AI INPUT)
# =========================================================

def test_empty_strings_rejected():
    with pytest.raises(ValidationError):
        Ticket.model_validate({
            "title": "",
            "description": "",
            "priority": "High",
            "labels": []
        })


def test_whitespace_strings():
    with pytest.raises(ValidationError):
        Ticket.model_validate({
            "title": "   ",
            "description": "   ",
            "priority": "High",
            "labels": []
        })


def test_unicode_input():
    ticket = Ticket.model_validate({
        "title": "🚨 Crash in login 🔐",
        "description": "Fails on submit 😵",
        "priority": "High",
        "labels": ["bug", "auth"]
    })

    assert "🚨" in ticket.title


# =========================================================
# COERCION BEHAVIOR (VERY IMPORTANT IN AI SYSTEMS)
# =========================================================

def test_labels_tuple_coercion():
    ticket = Ticket.model_validate({
        "title": "Bug",
        "description": "Crash",
        "priority": "High",
        "labels": ("bug", "auth")
    })

    assert isinstance(ticket.labels, list)


def test_labels_single_string_rejected():
    with pytest.raises(ValidationError):
        Ticket.model_validate({
            "title": "Bug",
            "description": "Crash",
            "priority": "High",
            "labels": "bug"
        })


# =========================================================
# SERIALIZATION / ROUNDTRIP
# =========================================================

def test_round_trip_model_dump():
    ticket = Ticket.model_validate(VALID_AI_OUTPUT)
    dumped = ticket.model_dump()
    rebuilt = Ticket.model_validate(dumped)

    assert rebuilt == ticket


def test_json_schema_stability():
    schema = Ticket.model_json_schema()

    assert schema["additionalProperties"] is False
    assert "title" in schema["properties"]
    assert "priority" in schema["properties"]


# =========================================================
# AI ROBUSTNESS
# =========================================================

def test_ai_partial_output_fails():
    partial = {
        "title": "Bug reported",
        "priority": "High"
    }

    with pytest.raises(ValidationError):
        Ticket.model_validate(partial)


def test_ai_noisy_extra_fields_fail():
    noisy = {
        **VALID_AI_OUTPUT,
        "confidence": 0.99,
        "source": "llm",
        "timestamp": "now"
    }

    with pytest.raises(ValidationError):
        Ticket.model_validate(noisy)


def test_ai_null_injection():
    with pytest.raises(ValidationError):
        Ticket.model_validate({
            "title": None,
            "description": None,
            "priority": "High",
            "labels": []
        })


# =========================================================
# OPTIONAL: FUZZ TESTING (HIGH VALUE FOR AI SYSTEMS)
# Requires: pip install hypothesis
# =========================================================

from hypothesis import given, strategies as st


@given(
    title=st.text(),
    description=st.text(),
    priority=st.sampled_from(["Low", "Medium", "High"]),
)
def test_fuzz_valid_structure(title, description, priority):
    """
    Ensures random valid-shaped inputs don't crash validation.
    """
    try:
        Ticket.model_validate({
            "title": title,
            "description": description,
            "priority": priority,
            "labels": []
        })
    except ValidationError:
        # only fail if schema rejects valid types unexpectedly
        pytest.fail("Valid structure rejected unexpectedly")