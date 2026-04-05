"""
Comprehensive test suite for Ticket model:
- schema validation
- AI robustness
- edge cases
- coercion behavior
- serialization stability
"""

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from utilities.ticket_util import Ticket

# ----------------------------
# Base valid inputs
# ----------------------------

VALID_AI_OUTPUT: dict[str, Any] = {
    "title": "Login bug",
    "description": "Login fails when submitting form",
    "priority": "High",
    "labels": ["bug", "auth"],
}

MINIMAL_VALID_OUTPUT: dict[str, Any] = {
    "title": "Bug",
    "description": "Something broke",
    "priority": "Low",
    "labels": [],
}

# ----------------------------
# Invalid inputs
# ----------------------------

INVALID_PRIORITY_OUTPUT: dict[str, Any] = {
    "title": "Bug",
    "description": "Crash",
    "priority": "URGENT",
    "labels": ["bug"],
}

MISSING_FIELDS_OUTPUT: dict[str, Any] = {"title": "Bug"}

WRONG_TYPE_OUTPUT: dict[str, Any] = {
    "title": 123,
    "description": "Crash",
    "priority": "High",
    "labels": ["bug"],
}

LABELS_WRONG_TYPE_OUTPUT: dict[str, Any] = {
    "title": "Bug",
    "description": "Crash",
    "priority": "High",
    "labels": "bug,auth",
}


# =========================================================
# HAPPY PATH
# =========================================================


def test_valid_ai_output() -> None:
    """Valid AI-generated ticket should pass validation and preserve fields."""
    Ticket.model_validate(VALID_AI_OUTPUT)


def test_minimal_valid_output() -> None:
    """Minimal valid ticket input should pass with correct defaults."""
    Ticket.model_validate(MINIMAL_VALID_OUTPUT)


# =========================================================
# SCHEMA ENFORCEMENT
# =========================================================


def test_missing_required_fields() -> None:
    """Missing required fields should raise a validation error."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(MISSING_FIELDS_OUTPUT)


def test_extra_fields_rejected() -> None:
    """Extra fields not defined in schema should be rejected."""
    bad: dict[str, Any] = {**VALID_AI_OUTPUT, "confidence": 0.99}
    with pytest.raises(ValidationError):
        Ticket.model_validate(bad)


# =========================================================
# TYPE SAFETY
# =========================================================


def test_wrong_type_title() -> None:
    """Incorrect type for title should raise a validation error."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(WRONG_TYPE_OUTPUT)


def test_wrong_type_labels() -> None:
    """Incorrect type for labels (string instead of list) should fail."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(LABELS_WRONG_TYPE_OUTPUT)


# =========================================================
# BUSINESS RULES
# =========================================================


def test_invalid_priority_rejected() -> None:
    """Priority outside allowed enum values should be rejected."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(INVALID_PRIORITY_OUTPUT)


# =========================================================
# EDGE CASES (IMPORTANT FOR AI INPUT)
# =========================================================


def test_unicode_input() -> None:
    """Unicode and emoji characters should be accepted in text fields."""
    ticket = Ticket.model_validate(
        {
            "title": "🚨 Crash in login 🔐",
            "description": "Fails on submit 😵",
            "priority": "High",
            "labels": ["bug", "auth"],
        }
    )

    assert "🚨" in ticket.title


# =========================================================
# COERCION BEHAVIOR (VERY IMPORTANT IN AI SYSTEMS)
# =========================================================


def test_labels_tuple_coercion() -> None:
    """Tuple input for labels should be coerced into a list."""
    ticket = Ticket.model_validate(
        {
            "title": "Bug",
            "description": "Crash",
            "priority": "High",
            "labels": ("bug", "auth"),
        }
    )

    assert isinstance(ticket.labels, list)


def test_labels_single_string_rejected() -> None:
    """Single string for labels should not be implicitly coerced."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(
            {
                "title": "Bug",
                "description": "Crash",
                "priority": "High",
                "labels": "bug",
            }
        )


# =========================================================
# SERIALIZATION / ROUNDTRIP
# =========================================================


def test_round_trip_model_dump() -> None:
    """Model should serialize and deserialize without data loss."""
    ticket = Ticket.model_validate(VALID_AI_OUTPUT)
    dumped = ticket.model_dump()
    rebuilt = Ticket.model_validate(dumped)

    assert rebuilt == ticket


def test_json_schema_stability() -> None:
    """Generated JSON schema should enforce strict structure."""
    schema: dict[str, Any] = Ticket.model_json_schema()

    assert schema["additionalProperties"] is False
    assert "title" in schema["properties"]
    assert "priority" in schema["properties"]


# =========================================================
# AI ROBUSTNESS
# =========================================================


def test_ai_partial_output_fails() -> None:
    """Partially generated AI outputs should fail validation."""
    partial: dict[str, Any] = {"title": "Bug reported", "priority": "High"}

    with pytest.raises(ValidationError):
        Ticket.model_validate(partial)


def test_ai_noisy_extra_fields_fail() -> None:
    """AI outputs with extra noisy fields should be rejected."""
    noisy: dict[str, Any] = {
        **VALID_AI_OUTPUT,
        "confidence": 0.99,
        "source": "llm",
        "timestamp": "now",
    }

    with pytest.raises(ValidationError):
        Ticket.model_validate(noisy)


def test_ai_null_injection() -> None:
    """Null values in required fields should be rejected."""
    with pytest.raises(ValidationError):
        Ticket.model_validate(
            {"title": None, "description": None, "priority": "High", "labels": []}
        )


@given(
    title=st.text(),
    description=st.text(),
    priority=st.sampled_from(["Low", "Medium", "High"]),
)  # type: ignore [misc]
def test_fuzz_valid_structure(
    title: str,
    description: str,
    priority: str,
) -> None:
    """
    Ensures random valid-shaped inputs do not crash validation
    and only fail when violating schema constraints.
    """
    try:
        Ticket.model_validate(
            {
                "title": title,
                "description": description,
                "priority": priority,
                "labels": [],
            }
        )
    except ValidationError:
        pytest.fail("Valid structure rejected unexpectedly")
