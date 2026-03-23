"""
    Front Desk Agent
"""

import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
You are an AI front desk assistant.

You MUST return JSON only.

Available actions:
- SHOW_MENU
- CREATE_DRAFT
- PUBLISH_TICKET
- SUMMARIZE_TICKET
- ASK_CLARIFICATION

Behavior:
- If user is unsure → SHOW_MENU
- If user wants draft → CREATE_DRAFT
- If user wants publish → PUBLISH_TICKET
- If user wants summary → SUMMARIZE_TICKET

Response format:
{
  "action": string,
  "message": string
}
"""


async def run_agent(message: str):
    """
    Run the front desk agent with the given message and history.
    """
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
    )

    text = response.output[0].content[0].text

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {
            "action": "SHOW_MENU",
            "message": "What would you like to do?\n- "
            "Create draft\n- Publish ticket\n- Summarize ticket",
        }
