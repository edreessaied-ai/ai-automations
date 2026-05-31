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


# Slack Message
@dataclass
class SlackMessage:
    """
    Represents a message to be sent to Slack.
    """
    text: str | None = None
    blocks: list[dict[str, Any]] | None = None
    response_type: Literal["ephemeral", "in_channel"] = "ephemeral"

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
        return payload
