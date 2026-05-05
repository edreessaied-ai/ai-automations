"""
    This module defines the pipeline for
    converting user input into structured
    tickets using an LLM.
"""
from domain.ticket.models import TicketIntent, TicketUserPromptText
from integrations.llm.openai_client import OpenAILLMClient

SYSTEM_PROMPT = """
You are an assistant that converts user
input into structured work items.

Your job is to transform messy, incomplete,
or unstructured input into a clean,
structured representation of a task or issue.

Return exactly ONE valid JSON object.
Do not include any text outside the JSON.

Output schema:
- title: concise summary of the task or issue
- description: clear explanation of the task or issue
- priority: one of ["Low", "Medium", "High"]
- labels: list of relevant tags (can be empty)

General Rules:
- Be concise and accurate
- Do not invent specific facts not implied by the input
- Do not include markdown, explanations, or code blocks

Structured Input Handling:
- If input contains clear details,
organize the description into logical
structure (Context, Impact, Steps, etc.)
- Only generalize when sufficient information is provided

Minimal or Vague Input Handling:
If the input lacks actionable detail:
- Use the input verbatim as the title
- Write a short 1-sentence neutral description
- Do not add structure or assume missing details
- Default priority to "Low"

Noise Handling:
If input contains irrelevant or mixed content:
- Focus only on information relevant to a task or issue

Priority Guidelines:
- High: blocking issue, system failure, urgent task
- Medium: meaningful work with some urgency or impact
- Low: minor task, unclear request, or non-urgent item
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
    ticket_intent = send_ticket_request_to_llm(user_input)
    return ticket_intent
