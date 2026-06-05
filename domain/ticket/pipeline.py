"""
    This module defines the pipeline for
    converting user input into structured
    tickets using an LLM.
"""
import asyncio
import json

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

# System prompt for turning a Slack thread discussion into a Jira ticket.
# Responsibilities mirror the "LLM Prompting Strategy" section of the
# Slack -> Jira Ticket Assistant design doc.
THREAD_SYSTEM_PROMPT = """
You convert a Slack thread discussion into a single, well-structured
Jira ticket.

Return exactly ONE valid JSON object. Do not include any text outside
the JSON.

Output schema:
- title: concise, specific ticket title (no trailing punctuation)
- description: structured explanation of the issue, grounded only in the
  thread. Preserve important technical details (services, errors,
  timestamps, deploys) mentioned in the conversation.
- priority: one of ["Low", "Medium", "High"]
- labels: list of relevant tags inferred from the discussion (can be empty)
- summary: one or two sentence plain-language summary of the issue
- assignee: null (do not assign anyone in the MVP)

You SHOULD:
- Identify the operational issue being discussed
- Ignore irrelevant chatter, greetings, and side conversations
- Produce a concise ticket title
- Generate a structured, readable description
- Infer the most likely priority from the impact described

You MUST NOT:
- Invent facts that are not present in the thread
- Overstate certainty
- Assume missing details

Priority Guidelines:
- High: outage, blocking issue, production impact, urgent operational pain
- Medium: meaningful work with moderate urgency or impact
- Low: unclear, informational, or non-urgent

If the user included instructions in their request (for example
"make this a high priority bug" or "summarize this into an incident
ticket"), honor them as long as they do not require inventing facts.
""".strip()

# Refinement prompts for the in-Slack Improve / Edit loop. Both operate on an
# existing draft (provided as JSON) and must preserve the output schema.
IMPROVE_SYSTEM_PROMPT = """
You improve an existing draft Jira ticket. You are given the current ticket
as a JSON object. Rewrite it to be clearer, better structured, and more
complete, while staying faithful to the original meaning.

Return exactly ONE valid JSON object. Do not include any text outside
the JSON.

Output schema:
- title: concise, specific ticket title (no trailing punctuation)
- description: clear, well-structured explanation of the issue
- priority: one of ["Low", "Medium", "High"]
- labels: list of relevant tags (can be empty)
- summary: one or two sentence plain-language summary
- assignee: keep the existing value (null if absent)

You SHOULD:
- Improve clarity, grammar, structure, and completeness
- Preserve all concrete technical details already present
- Keep the same priority unless the existing text clearly justifies a change

You MUST NOT:
- Invent facts, services, errors, or impact not implied by the current draft
- Change the fundamental issue the ticket describes
""".strip()

EDIT_SYSTEM_PROMPT = """
You edit an existing draft Jira ticket according to a user's instruction.
You are given the current ticket as a JSON object and a natural-language
instruction describing the change the user wants.

Return exactly ONE valid JSON object. Do not include any text outside
the JSON.

Output schema:
- title: concise, specific ticket title (no trailing punctuation)
- description: clear, well-structured explanation of the issue
- priority: one of ["Low", "Medium", "High"]
- labels: list of relevant tags (can be empty)
- summary: one or two sentence plain-language summary
- assignee: keep the existing value unless the instruction changes it

Rules:
- Apply the user's instruction faithfully and precisely
- Leave everything the instruction does not mention unchanged
- Do not invent facts beyond what the instruction or current draft imply
""".strip()

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


def _build_thread_prompt(
    thread_text: str,
    user_instructions: str | None,
) -> str:
    """
    Combine the cleaned thread transcript with any user instructions
    from the bot mention into a single LLM prompt.
    """
    instructions = (user_instructions or "").strip()
    instruction_block = (
        f"User instructions: {instructions}"
        if instructions
        else "User instructions: (none provided)"
    )
    return (
        f"{instruction_block}\n\n"
        "Slack thread (chronological order):\n"
        f"{thread_text}"
    )


async def create_ticket_intent_from_thread(
    thread_text: str,
    user_instructions: str | None = None,
) -> TicketIntent:
    """
    Build a structured TicketIntent from a cleaned Slack thread transcript
    plus any instructions included in the bot mention.
    """
    log_handler.info("Creating ticket intent from Slack thread context.")
    prompt = _build_thread_prompt(thread_text, user_instructions)
    ticket_intent = llm_client.extract_structured(
        prompt=prompt,
        system_prompt=THREAD_SYSTEM_PROMPT,
        data_model=TicketIntent,
        max_retries=5,
    )
    log_handler.info(
        f"Received thread ticket intent from LLM: {ticket_intent.to_string()}"
    )
    return ticket_intent


def _refine(system_prompt: str, prompt: str) -> TicketIntent:
    """Run a refinement prompt through the LLM and return a TicketIntent."""
    return llm_client.extract_structured(
        prompt=prompt,
        system_prompt=system_prompt,
        data_model=TicketIntent,
        max_retries=5,
    )


async def improve_ticket_intent(intent: TicketIntent) -> TicketIntent:
    """
    Enhance an existing draft's clarity, structure, and completeness without
    inventing new facts (the "Improve" button).
    """
    log_handler.info("Improving existing ticket draft.")
    prompt = f"Current ticket:\n{json.dumps(intent.to_dict())}"
    # extract_structured is blocking I/O; keep it off the event loop.
    return await asyncio.to_thread(_refine, IMPROVE_SYSTEM_PROMPT, prompt)


async def edit_ticket_intent(
    intent: TicketIntent,
    instructions: str,
) -> TicketIntent:
    """
    Apply a natural-language instruction to an existing draft (the "Edit"
    modal), e.g. "make it medium priority and mention mobile impact".
    """
    log_handler.info(f"Editing ticket draft with instructions: {instructions}")
    prompt = (
        f"Current ticket:\n{json.dumps(intent.to_dict())}\n\n"
        f"User instruction: {instructions}"
    )
    return await asyncio.to_thread(_refine, EDIT_SYSTEM_PROMPT, prompt)
