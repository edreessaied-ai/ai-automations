"""
    Slack command parser for converting raw
    Slack payloads into structured internal request models.
"""
import re
from typing import Any

import integrations.slack.models as models
from utilities.logger import get_logger

log_handler = get_logger(__name__)

# `<@U123456>` style user mentions.
_USER_MENTION_RE = re.compile(r"<@([A-Z0-9]+)(?:\|[^>]+)?>")
# `<http://example.com|label>` or `<http://example.com>` style links.
_LINK_RE = re.compile(r"<(https?://[^|>]+)(?:\|([^>]+))?>")
# `<!channel>` / `<!here>` style special mentions.
_SPECIAL_MENTION_RE = re.compile(r"<!([^>|]+)(?:\|[^>]+)?>")


def normalize_slack_command(slack_command_str: str) -> models.SlackRequestType:
    """
    Normalize the incoming Slack command by
    stripping leading/trailing slash
    """
    formatted_slack_request = slack_command_str.lstrip("/")
    try:
        return models.SlackRequestType(formatted_slack_request)
    except ValueError:
        log_handler.error(f"Unknown Slack command: {formatted_slack_request}")
        return models.SlackRequestType.UNKNOWN_COMMAND


def build_slack_command_request(
    payload: models.UnnormalizedSlackRequest
) -> models.NormalizedSlackCommandRequest:
    """
    Convert raw Slack payload → internal request model.
    """
    command = str(payload.get("command") or "")
    normalized_command = normalize_slack_command(command)
    return models.NormalizedSlackCommandRequest(
        intent=normalized_command,
        text=payload.get("text"),
        user_id=payload.get("user_id"),
        channel_id=payload.get("channel_id"),
        response_url=payload.get("response_url"),
        thread_ts=payload.get("thread_ts"),
    )


def _normalize_slack_formatting(text: str) -> str:
    """
    Strip excessive Slack markup so the LLM sees clean conversational text.

    - User mentions `<@U123>` become `@user`
    - Links `<url|label>` become their label (or the bare url)
    - Special mentions `<!here>` become `@here`
    - HTML entities Slack escapes are unescaped
    """
    text = _USER_MENTION_RE.sub("@user", text)
    text = _LINK_RE.sub(lambda m: m.group(2) or m.group(1), text)
    text = _SPECIAL_MENTION_RE.sub(lambda m: f"@{m.group(1)}", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return text.strip()


def extract_user_instructions(text: str) -> str:
    """
    Remove the leading bot mention from an app_mention's text, leaving only
    the instructions the user typed (e.g. "create a high priority bug ticket").
    """
    without_mentions = _USER_MENTION_RE.sub("", text)
    # The simulator may send a plain "@TicketBot" handle instead of a real id.
    without_mentions = re.sub(r"@\w+", "", without_mentions, count=1)
    return without_mentions.strip()


def parse_app_mention_event(event: dict[str, Any]) -> models.AppMentionEvent:
    """
    Convert a raw Slack `app_mention` event into a normalized model.
    """
    return models.AppMentionEvent(
        channel_id=str(event.get("channel") or ""),
        user_id=event.get("user"),
        text=str(event.get("text") or ""),
        thread_ts=event.get("thread_ts"),
        event_ts=str(event.get("event_ts") or event.get("ts") or ""),
    )


def clean_thread_to_text(context: models.SlackThreadContext) -> str:
    """
    Render thread context into a clean, chronological transcript for the LLM.

    Per the design doc this performs light cleaning only (normalize usernames,
    strip excessive formatting, preserve ordering) and does NOT pre-summarize.
    """
    lines: list[str] = []
    for message in context.messages:
        cleaned = _normalize_slack_formatting(message.text)
        if not cleaned:
            continue
        speaker = f"@{message.user}" if message.user else "@unknown"
        lines.append(f"{speaker}: {cleaned}")
    return "\n".join(lines)


def parse_interaction_payload(
    payload: dict[str, Any],
) -> models.SlackInteractionAction:
    """
    Normalize an interactive button payload (Slack `block_actions` or the
    local simulator) into a SlackInteractionAction.
    """
    # Local simulator sends a flat payload; Slack nests under `actions`.
    actions = payload.get("actions")
    if isinstance(actions, list) and actions:
        first_action = actions[0]
        action_id = str(first_action.get("action_id") or "")
        draft_id = str(first_action.get("value") or "")
    else:
        action_id = str(payload.get("action") or "")
        draft_id = str(payload.get("draft_id") or "")

    user = payload.get("user")
    user_id = user.get("id") if isinstance(user, dict) else payload.get(
        "user_id"
    )

    return models.SlackInteractionAction(
        action=models.SlackActionType(action_id),
        draft_id=draft_id,
        response_url=payload.get("response_url"),
        user_id=user_id,
    )
