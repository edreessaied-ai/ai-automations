"""
Front Desk Agent
"""

import json
import os
from typing import Any

from openai import OpenAI

from utilities.type_util import Json

# ----------------------------
# OpenAI setup
# ----------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------
# Prompt
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

# ----------------------------
# Public API
# ----------------------------


async def run_agent(message: str) -> Json:
    """
    Run the front desk agent with the given message.
    """
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    )

    text = response.output[0].content[0].text

    try:
        parsed: Any = json.loads(text)

        if not isinstance(parsed, dict):
            raise ValueError("LLM output is not a Json object")

        return parsed

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing Json: {e}")
        return {
            "action": "SHOW_MENU",
            "message": (
                "What would you like to do?\n- "
                "Create draft\n- Publish ticket\n- Summarize ticket"
            ),
        }
