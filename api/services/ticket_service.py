"""
TicketService

This service is responsible for all AI-powered ticket operations:
- Generating Jira tickets from raw text
- Improving ticket structure and clarity
- Editing tickets using natural language instructions

It is the core "AI reasoning layer" of the system and is designed
to be reused across CLI, API, Slack bots, etc.

This module isolates:
- OpenAI calls
- Prompt engineering
- JSON schema enforcement
- response parsing
"""

import json
from typing import Any

from openai import OpenAI

from utilities.ticket_util import Ticket, pretty_print_ticket
from utilities.type_util import JsonSchema


class TicketService:
    """
    AI-powered service for generating and modifying Jira tickets.
    """

    def __init__(
        self, model: str = "gpt-4.1-mini", api_key: str | None = None
    ) -> None:
        """
        Initialize TicketService.

        Args:
            model: OpenAI model used for ticket generation.
            api_key: Optional API key override. If not provided,
                     environment variable is used by OpenAI client.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    # =========================================================
    # System Prompt
    # =========================================================

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
  (Context, Impact, Steps to Reproduce)

Vague Input Handling (OVERRIDES ALL OTHER RULES):
If the input is vague, unclear, or non-actionable:
- Use the input verbatim as the title
- Write a short, neutral description (1 sentence max)
- Default priority to "Low"

If the input contains irrelevant content:
- Focus only on actionable parts
"""

    # =========================================================
    # JSON Schema
    # =========================================================

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

    # =========================================================
    # Core LLM Call
    # =========================================================

    def _create_ticket_from_llm(self, prompt: str) -> Ticket:
        """
        Send prompt to OpenAI and return a structured Ticket.

        This is the single unified entry point for all ticket operations.
        """

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ticket",
                    "schema": self.TICKET_SCHEMA,
                    "strict": True,
                }
            },
        )

        raw_json = response.output[0].content[0].text
        parsed = json.loads(raw_json)

        parsed = self._decode_escapes(parsed)

        return Ticket(**parsed)

    # =========================================================
    # Utilities
    # =========================================================

    def _decode_escapes(self, obj: Any) -> Any:
        """
        Recursively decode unicode escape sequences in LLM output.

        This ensures text like "\\n" or "\\uXXXX" is properly interpreted.
        """
        if isinstance(obj, str):
            return obj.encode("utf-8").decode("unicode_escape")

        if isinstance(obj, dict):
            return {k: self._decode_escapes(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [self._decode_escapes(v) for v in obj]

        return obj

    # =========================================================
    # Public API
    # =========================================================

    def generate(self, user_input: str) -> Ticket:
        """
        Convert raw user input into a structured Jira ticket.

        This is the entry point for new ticket creation.
        """
        prompt = f"""
Convert the following into a structured Jira ticket:

{user_input}
"""
        return self._create_ticket_from_llm(prompt)

    def improve(self, ticket: Ticket) -> Ticket:
        """
        Improve an existing ticket by enhancing clarity,
        structure, and completeness without changing intent.
        """
        prompt = f"""
Improve the following Jira ticket.

Make it clearer, more structured, and more complete
while preserving the original intent.

Ticket:
{pretty_print_ticket(ticket)}
"""
        return self._create_ticket_from_llm(prompt)

    def edit(self, ticket: Ticket, instruction: str) -> Ticket:
        """
        Modify a ticket based on a natural language instruction.

        Example:
            "make this high priority and add mobile impact"
        """
        prompt = f"""
Update the following Jira ticket based on the instruction.

Instruction:
{instruction}

Current Ticket:
{pretty_print_ticket(ticket)}

Return the fully updated ticket.
"""
        return self._create_ticket_from_llm(prompt)
