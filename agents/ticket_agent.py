#!/usr/bin/env python3
"""
Ticket Agent CLI
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from utilities.logger import get_logger
from utilities.ticket_util import Ticket, pretty_print_ticket
from utilities.type_util import JsonSchema

ticket_agent_logger = get_logger("ticket_agent")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Helpers
# =========================


def load_input_file(file_path: str) -> str:
    """Read raw input text from a file."""
    return Path(file_path).read_text(encoding="utf-8").strip()


SYSTEM_PROMPT = """
You are an assistant that converts user input into high-quality Jira tickets.

Your job is to transform messy, incomplete,
or unstructured input into a clean, structured ticket.

Output MUST be valid JSON with the following fields:
- title: a concise summary of the issue
- description: a clear explanation of the issue
- priority: one of ["Low", "Medium", "High"]
- labels: a list of relevant tags (can be empty)

General Guidelines:
- Be concise but clear
- Do not invent specific facts that are not implied
- Do NOT include any text outside the JSON

Structured Input Handling:
- If the input contains clear details, structure the description
    (e.g., Context, Impact, Steps to Reproduce)
- You may make reasonable generalizations ONLY when the
    input is sufficiently detailed

Vague Input Handling (OVERRIDES ALL OTHER RULES):
If the input is vague, unclear, or non-actionable:
- DO NOT mention that the input is unclear
- DO NOT ask for clarification
- DO NOT explain missing details
- DO NOT add structure (no sections)

Instead:
- Use the input verbatim as the title
- Write a short, neutral description (1 sentence max)
- Keep the output minimal and literal
- Default priority to "Low"

If the input contains irrelevant,
nonsensical, or offensive content:
- Ignore unrelated or non-actionable portions
- Focus only on extracting the actionable issue
"""

TICKET_SCHEMA: JsonSchema = {
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


def send_ticket_request_to_llm(user_prompt: str) -> Ticket:
    """
    Send a request to the LLM to generate a ticket based on the user prompt.
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

    def _decode_escapes(obj: Any) -> Any:
        """
        Recursively decode escape sequences in
        a JSON object.
        """
        if isinstance(obj, str):
            return obj.encode("utf-8").decode("unicode_escape")
        if isinstance(obj, dict):
            return {k: _decode_escapes(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_decode_escapes(v) for v in obj]
        return obj

    # parsed is the final dict with all escape sequences decoded
    parsed = _decode_escapes(json.loads(response.output[0].content[0].text))
    return Ticket(**parsed)


# =========================
# Public Functions
# =========================


def generate_ticket(user_input: str) -> Ticket:
    """
    Convert messy user input into a structured Jira ticket.
    """
    prompt = f"""
Convert the following into a structured Jira ticket:

{user_input}
"""
    return send_ticket_request_to_llm(prompt)


def improve_ticket(current_ticket: Ticket) -> Ticket:
    """
    Improve an existing ticket by enhancing clarity,
    structure, and completeness.
    """
    prompt = f"""
Improve the following Jira ticket. Make it clearer, more structured,
and more complete, while preserving the original intent.

Ticket:
{pretty_print_ticket(current_ticket)}
"""
    return send_ticket_request_to_llm(prompt)


def edit_ticket(current_ticket: Ticket, instruction: str) -> Ticket:
    """
    Modify a ticket based on a natural language instruction.
    """
    prompt = f"""
Update the following Jira ticket based on the user's instruction.

Instruction:
{instruction}

Current Ticket:
{pretty_print_ticket(current_ticket)}

Return the fully updated ticket.
"""
    return send_ticket_request_to_llm(prompt)


def create_ticket_in_jira(ticket: Ticket, project_key: str) -> dict[str, str]:
    """
    Create a ticket in Jira based on the provided ticket data and project key.
    Placeholder implementation - replace with actual Jira API call.
    """
    # Placeholder implementation - replace with actual Jira API call
    return {
        "message": f"Ticket created in project "
        f"{project_key} with title: {ticket.title}"
    }


# =========================
# Main Ticket Agent CLI
# =========================


def ticket_agent() -> None:
    """
    CLI for the Ticket Agent.
    """
    parser = argparse.ArgumentParser(description="Ticket Agent CLI")
    parser.add_argument("file", help="Path to input text file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate-ticket", action="store_true")
    group.add_argument("--improve-ticket", action="store_true")
    group.add_argument("--edit-ticket", action="store_true")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print the raw JSON output"
    )

    parser.add_argument(
        "--edit-prompt",
        type=str,
        default=None,
        help="Edit instruction (required for --edit-ticket)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output file path",
    )

    args = parser.parse_args()

    # Load input
    input_content = load_input_file(args.file)

    ticket_agent_logger.info("Loaded input from file: %s", args.file)
    ticket_agent_logger.info("Input content: %s", input_content)

    result: Ticket

    # =========================
    # Execute action
    # =========================

    if args.generate_ticket:
        ticket_agent_logger.info("Generating ticket...")
        result = generate_ticket(input_content)

    elif args.improve_ticket:
        ticket_agent_logger.info("Generating + improving ticket...")
        ticket = generate_ticket(input_content)
        result = improve_ticket(ticket)

    elif args.edit_ticket:
        if not args.edit_prompt:
            raise ValueError("--edit-prompt is required for --edit-ticket")

        ticket_agent_logger.info("Generating + improving + editing ticket...")
        ticket = generate_ticket(input_content)
        improved = improve_ticket(ticket)
        result = edit_ticket(improved, args.edit_prompt)

    else:
        raise ValueError("No valid action provided")

    # =========================
    # Output
    # =========================

    ticket_agent_logger.info("Final result:")
    pretty_printed_res = pretty_print_ticket(result)
    ticket_agent_logger.info(pretty_printed_res)
    if args.verbose:
        print(pretty_printed_res)


if __name__ == "__main__":
    ticket_agent()
