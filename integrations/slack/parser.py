"""
    Slack command parser for converting raw
    Slack payloads into structured internal request models.
"""
import integrations.slack.models as models
from utilities.logger import get_logger

log_handler = get_logger(__name__)


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
