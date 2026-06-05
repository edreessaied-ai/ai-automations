"""
Slack Models - Defines the data structures for representing Slack-related data.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel
from pydantic.networks import HttpUrl

# Slack specific types
SlackTimestampStr = str
SlackChannelIDStr = str
SlackUserIDStr = str
SlackInputTextStr = str
UnnormalizedSlackRequest = dict[str, Any]


class SlackRequestType(StrEnum):
    """
    Defines the types of requests we can receive from Slack.
    This helps us route the request to the appropriate handler.
    """
    CREATE_TICKET = "create-ticket"
    IMPROVE_TICKET = "improve-ticket"
    SUMMARIZE_THREAD = "summarize-thread"
    UNKNOWN_COMMAND = "unknown command"


class SlackActionType(StrEnum):
    """
    Interactive Block Kit action ids used by the draft preview buttons.
    """
    CONFIRM_TICKET = "confirm_ticket"
    CANCEL_TICKET = "cancel_ticket"
    IMPROVE_TICKET = "improve_ticket"
    EDIT_TICKET = "edit_ticket"


# Block Kit identifiers for the natural-language "Edit" modal.
EDIT_MODAL_CALLBACK_ID = "edit_ticket_modal"
EDIT_MODAL_BLOCK_ID = "edit_instructions_block"
EDIT_MODAL_ACTION_ID = "edit_instructions_input"


class NormalizedSlackCommandRequest(BaseModel):
    """
    Normalized request from Slack to backend.
    """
    intent: SlackRequestType | None
    text: SlackInputTextStr | None
    user_id: SlackUserIDStr | None
    channel_id: SlackChannelIDStr | None
    response_url: HttpUrl | None = None
    # Thread timestamp is optional
    # because not all commands will be issued from a thread
    thread_ts: SlackTimestampStr | None


# Slack Response Payload
class SlackResponsePayload(TypedDict, total=False):
    """
    Represents the payload for a Slack response.
    """
    text: str
    blocks: list[dict[str, Any]]
    response_type: Literal["ephemeral", "in_channel"]
    # When sent to an interaction `response_url`, replaces the original message
    # in place instead of posting a new one (used by the Improve/Edit loop).
    replace_original: bool


# Slack Message
@dataclass
class SlackMessage:
    """
    Represents a message to be sent to Slack.
    """
    text: str | None = None
    blocks: list[dict[str, Any]] | None = None
    response_type: Literal["ephemeral", "in_channel"] = "ephemeral"
    replace_original: bool = False

    def to_slack_response(self) -> SlackResponsePayload:
        """
        Converts the SlackMessage into a Slack-compatible response payload.
        """
        payload: SlackResponsePayload = {
            "response_type": self.response_type
        }
        if self.text is not None:
            payload["text"] = self.text
        if self.blocks is not None:
            payload["blocks"] = self.blocks
        if self.replace_original:
            payload["replace_original"] = True
        return payload


class SlackThreadMessage(BaseModel):
    """
    A single message retrieved from a Slack thread.

    Mirrors the SlackMessage internal model from the design doc
    (user / text / timestamp).
    """
    user: str
    text: str
    timestamp: SlackTimestampStr


class SlackThreadContext(BaseModel):
    """
    Thread-scoped context gathered for an explicit bot mention.

    This is the only context the assistant is allowed to reason over in
    the MVP: a single thread the user explicitly invoked the bot in.
    """
    channel_id: SlackChannelIDStr
    thread_ts: SlackTimestampStr
    messages: list[SlackThreadMessage]


class AppMentionEvent(BaseModel):
    """
    Normalized representation of a Slack `app_mention` event.

    `thread_ts` is optional: a mention posted directly in a channel (not in
    a thread) has no thread context, which the MVP explicitly rejects.
    """
    channel_id: SlackChannelIDStr
    user_id: SlackUserIDStr | None
    text: SlackInputTextStr
    thread_ts: SlackTimestampStr | None
    event_ts: SlackTimestampStr


class SlackInteractionAction(BaseModel):
    """
    Normalized representation of an interactive button click coming back
    from Slack (or the local simulator).
    """
    action: SlackActionType
    draft_id: str
    response_url: HttpUrl | None = None
    user_id: SlackUserIDStr | None = None
    # Required to open a modal (`views.open`) in response to a button click.
    # Slack issues a short-lived trigger id with every interaction payload.
    trigger_id: str | None = None


class SlackViewSubmission(BaseModel):
    """
    Normalized representation of an "Edit" modal submission (`view_submission`).

    The draft id is round-tripped through the modal's `private_metadata`, and
    the free-text instructions come from the modal's single input block.
    """
    draft_id: str
    instructions: str
    user_id: SlackUserIDStr | None = None
