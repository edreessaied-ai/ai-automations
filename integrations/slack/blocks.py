"""
Block Kit builders for the Slack -> Jira draft confirmation flow.

The draft preview (Step 5 in the design doc) is the critical human-in-the-loop
checkpoint: the bot never creates a Jira ticket until the user clicks
"Create Ticket".
"""
from typing import Any

import integrations.slack.models as models
from domain.ticket.models import TicketIntent
from integrations.jira.models import JiraInstance

# User-facing copy for the error states described in the design doc.
OUTSIDE_THREAD_MESSAGE = (
    "Please invoke me inside a Slack thread so I can gather "
    "conversation context."
)
LLM_FAILURE_MESSAGE = (
    "I couldn't confidently generate a ticket from this discussion. "
    "Please try again with more context."
)
JIRA_FAILURE_MESSAGE = (
    "Failed to create Jira ticket. Please try again later."
)
DRAFT_EXPIRED_MESSAGE = (
    "This draft is no longer available. Please mention me again in the "
    "thread to generate a fresh ticket."
)


def _section(text: str) -> dict[str, Any]:
    """Build a markdown section block."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }


def build_draft_preview_blocks(
    intent: TicketIntent,
    draft_id: str,
) -> list[dict[str, Any]]:
    """
    Build the "Proposed Jira Ticket" draft preview with Create/Cancel buttons.

    The draft id is carried in each button's `value` so the interaction
    handler can recover the exact draft the user is confirming.
    """
    priority = (intent.priority or "Low").capitalize()
    summary = intent.summary or intent.description or "_No summary available._"

    blocks: list[dict[str, Any]] = [
        _section(":memo: *Proposed Jira Ticket*"),
        _section(f"*Title:*\n{intent.title or 'Untitled'}"),
        _section(f"*Priority:*\n{priority}"),
        _section(f"*Summary:*\n{summary}"),
    ]

    if intent.labels:
        blocks.append(_section(f"*Labels:* {', '.join(intent.labels)}"))

    blocks.append(
        {
            "type": "actions",
            "block_id": f"ticket_draft:{draft_id}",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Create Ticket"},
                    "action_id": models.SlackActionType.CONFIRM_TICKET.value,
                    "value": draft_id,
                },
                {
                    "type": "button",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Cancel"},
                    "action_id": models.SlackActionType.CANCEL_TICKET.value,
                    "value": draft_id,
                },
            ],
        }
    )
    return blocks


def build_creation_success_message(
    jira_instance: JiraInstance,
) -> models.SlackMessage:
    """Build the confirmation message shown after a ticket is created."""
    text = (
        f":white_check_mark: *Created Jira Ticket: "
        f"{jira_instance.issue_key}*\n{jira_instance.issue_url}"
    )
    return models.SlackMessage(
        text=text,
        blocks=[_section(text)],
        response_type="in_channel",
    )


def build_cancelled_message() -> models.SlackMessage:
    """Build the message shown when the user cancels a draft."""
    text = ":wave: No problem — I won't create that ticket."
    return models.SlackMessage(text=text, blocks=[_section(text)])


def build_error_message(text: str) -> models.SlackMessage:
    """Build a simple ephemeral error message."""
    return models.SlackMessage(
        text=f":warning: {text}",
        blocks=[_section(f":warning: {text}")],
    )
