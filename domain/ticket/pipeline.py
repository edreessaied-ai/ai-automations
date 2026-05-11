"""
    This module defines the pipeline for
    converting user input into structured
    tickets using an LLM.
"""
from domain.ticket.models import TicketIntent, TicketUserPromptText
from integrations.llm.openai_client import OpenAILLMClient
from utilities.logger import get_logger

log_handler = get_logger(__name__)


SYSTEM_PROMPT = """
You are an assistant that converts raw input
into structured work items.

Your job is to transform messy, incomplete,
or unstructured input into a clean,
concise, structured task representation.

Return exactly ONE valid JSON object.
Do not include any text outside the JSON.

Output schema:
- title: concise summary of the task or issue
- description: clear explanation of the task or issue
- priority: one of ["Low", "Medium", "High"]
- labels: list of relevant tags (can be empty)

Core Behavior:
- Speak directly and naturally
- Write as if you are responding only to the person who submitted the input
- Never refer to:
  - "the user"
  - "the requester"
  - "the customer"
  - "they"
  - any third-party observer
- Never describe what someone "claims", "states", or "reports"
- Do not narrate or analyze the input from the outside
- Do not sound like an analyst writing notes for another team

General Rules:
- Be concise and accurate
- Do not invent details not implied by the input
- Do not include markdown, explanations, or code blocks
- Preserve the original intent and tone when possible
- Prefer simple, direct wording

Structured Input Handling:
- If the input contains actionable details,
organize them clearly and professionally
- Add light structure only when useful
- Do not force structure onto casual or minimal input

Minimal or Vague Input Handling:
If the input lacks actionable detail:
- Use the input verbatim or lightly cleaned as the title
- Write a short neutral description
- Do not reinterpret jokes, slang, or casual statements
- Do not invent context or implied problems
- Default priority to "Low"

Noise Handling:
If the input contains irrelevant or mixed content:
- Focus only on information relevant to a task or issue

Priority Guidelines:
- High: blocking issue, outage, urgent operational impact
- Medium: meaningful work with moderate urgency or impact
- Low: unclear request, casual input, informational note, or non-urgent issue
"""

llm_client = OpenAILLMClient()


def send_ticket_request_to_llm(
    user_prompt: str,
) -> TicketIntent:
    """
    Send a request to the LLM to generate a ticket based on the user prompt.
    """
    return llm_client.extract_structured(
        prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        data_model=TicketIntent,
        max_retries=5,
    )


async def create_ticket_intent_from_user_input(
    user_input: TicketUserPromptText
) -> TicketIntent:
    """
    Main pipeline function to create a TicketIntent from user input.
    """
    log_handler.info(
        f"Creating ticket intent from user input: {user_input}"
    )
    ticket_intent = send_ticket_request_to_llm(user_input)
    ticket_intent_str = ticket_intent.to_string()
    log_handler.info(
        f"Received ticket intent from LLM: {ticket_intent_str}"
    )
    return ticket_intent
