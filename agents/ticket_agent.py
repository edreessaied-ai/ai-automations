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
from typing import Dict, Any

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


SYSTEM_PROMPT = """
You are an assistant that converts user input into high-quality Jira tickets.

Your job is to transform messy, incomplete, or
unstructured input into a clean, structured ticket.

Output MUST be valid JSON with the following fields:
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
- Do NOT include any text outside the JSON

If the input already contains structure (e.g., Title:, Description:), use it.
Otherwise, infer structure from the input.
"""

TICKET_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "priority": {
            "type": "string",
            "enum": ["Low", "Medium", "High"]
        },
        "labels": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["title", "description", "priority", "labels"],
    "additionalProperties": False
}


def _call_llm(user_prompt: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "ticket",
                "schema": TICKET_SCHEMA,
                "strict": True
            }
        }
    )
    return json.loads(response.output[0].content[0].text)

# =========================
# Public Functions
# =========================


def generate_ticket(user_input: str) -> Dict[str, Any]:
    """
    Convert messy user input into a structured Jira ticket.
    """
    prompt = f"""
Convert the following into a structured Jira ticket:

{user_input}
"""
    return _call_llm(prompt)


def improve_ticket(current_ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Improve an existing ticket by enhancing clarity,
    structure, and completeness.
    """
    prompt = f"""
Improve the following Jira ticket. Make it clearer, more structured, =
and more complete, while preserving the original intent.

Ticket:
{json.dumps(current_ticket, indent=2)}
"""
    return _call_llm(prompt)


def edit_ticket(
    current_ticket: Dict[str, Any],
    instruction: str
) -> Dict[str, Any]:
    """
    Modify a ticket based on a natural language instruction.
    """
    prompt = f"""
Update the following Jira ticket based on the user's instruction.

Instruction:
{instruction}

Current Ticket:
{json.dumps(current_ticket, indent=2)}

Return the fully updated ticket.
"""
    return _call_llm(prompt)


# =========================
# Local Testing
# =========================

if __name__ == "__main__":
    # Example test cases

    print("=== GENERATE ===")
    ticket = generate_ticket("payments failing for EU users after deploy")
    print(json.dumps(ticket, indent=2))

    print("\n=== IMPROVE ===")
    improved = improve_ticket(ticket)
    print(json.dumps(improved, indent=2))

    print("\n=== EDIT ===")
    edited = edit_ticket(
        improved,
        "lower priority to medium and mention mobile users"
    )
    print(json.dumps(edited, indent=2))
