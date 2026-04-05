#!/usr/bin/env python3
"""
ticket_agent.py

Core AI logic for:
- Generating Jira tickets from messy input
- Improving existing tickets
- Editing tickets via natural language instructions
"""

import json
import os
from typing import Any

from openai import OpenAI

from utilities.logger import get_hourly_logger, pretty_print_json
from utilities.type_util import Json

ticket_agent_logger = get_hourly_logger("ticket_agent")

# ----------------------------
# Typing
# ----------------------------


# ----------------------------
# OpenAI setup
# ----------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Prompt + Schema
# ----------------------------

SYSTEM_PROMPT = """
You are an assistant that converts user input into high-quality Jira tickets.

Your job is to transform messy, incomplete, or
unstructured input into a clean, structured ticket.

Output MUST be valid Json with the following fields:
- title: a concise summary of the issue
- description: a clear, structured explanation of the issue
- priority: one of ["Low", "Medium", "High"]
- labels: a list of relevant tags (can be empty)

Guidelines:
- Be concise but clear
- Do not invent specific facts that are not implied
- If details are missing, make reasonable generalizations
- Structure the description with sections when helpful
(e.g., Context, Impact, Steps to Reproduce)
- Prioritize clarity over verbosity
- Do NOT include any text outside the Json

If the input already contains structure (e.g., Title:, Description:), use it.
Otherwise, infer structure from the input.
"""

TICKET_SCHEMA: Json = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "labels": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "description", "priority", "labels"],
    "additionalProperties": False,
}

# ----------------------------
# Internal Helpers
# ----------------------------


def _decode_escapes(obj: Any) -> Any:
    """
    Recursively decodes escape sequences in a nested Json-like structure.
    """
    if isinstance(obj, str):
        return obj.replace("\\n", "\n")
    if isinstance(obj, dict):
        return {k: _decode_escapes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_escapes(v) for v in obj]
    return obj


def _call_llm(user_prompt: str) -> Json:
    """
    Calls the LLM and enforces that output is a Json object.
    """
    response = OPENAI_CLIENT.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "ticket",
                "schema": TICKET_SCHEMA,
                "strict": True,
            }
        },
    )

    parsed = json.loads(response.output[0].content[0].text)
    decoded = _decode_escapes(parsed)

    if not isinstance(decoded, dict):
        raise ValueError("LLM did not return a Json object")

    return decoded


# =========================
# Public Functions
# =========================


def generate_ticket(user_input: str) -> Json:
    """
    Convert messy user input into a structured Jira ticket.
    """
    prompt = f"""
Convert the following into a structured Jira ticket:

{user_input}
"""
    return _call_llm(prompt)


def improve_ticket(current_ticket: Json) -> Json:
    """
    Improve an existing ticket by enhancing clarity,
    structure, and completeness.
    """
    prompt = f"""
Improve the following Jira ticket. Make it clearer, more structured,
and more complete, while preserving the original intent.

Ticket:
{pretty_print_json(current_ticket)}
"""
    return _call_llm(prompt)


def edit_ticket(current_ticket: Json, instruction: str) -> Json:
    """
    Modify a ticket based on a natural language instruction.
    """
    prompt = f"""
Update the following Jira ticket based on the user's instruction.

Instruction:
{instruction}

Current Ticket:
{pretty_print_json(current_ticket)}

Return the fully updated ticket.
"""
    return _call_llm(prompt)


# =========================
# Local Testing
# =========================

if __name__ == "__main__":
    ticket_agent_logger.info("Starting ticket agent tests...")

    input_content = "payments failing for EU users after deploy"
    ticket_agent_logger.info("Input content: %s", input_content)

    # Generate ticket
    ticket_agent_logger.info("Generating ticket...")
    ticket = generate_ticket(input_content)
    ticket_agent_logger.info("Generated ticket:")
    ticket_agent_logger.info(pretty_print_json(ticket))

    # Improve ticket
    ticket_agent_logger.info("Improving ticket...")
    improved_ticket = improve_ticket(ticket)
    ticket_agent_logger.info("Improved ticket:")
    ticket_agent_logger.info(pretty_print_json(improved_ticket))

    # Edit ticket
    ticket_agent_logger.info("Editing ticket...")
    edited_ticket = edit_ticket(
        improved_ticket,
        "lower priority to medium and mention mobile users",
    )
    ticket_agent_logger.info("Edited ticket:")
    ticket_agent_logger.info(pretty_print_json(edited_ticket))

    ticket_agent_logger.info("Tests complete.")
