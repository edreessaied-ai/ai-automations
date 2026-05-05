"""
    Slack command dispatcher for processing incoming Slack commands.
"""
from collections.abc import Callable

import integrations.slack.client as client
import integrations.slack.models as models
import utilities.logger as logger
from domain.ticket.pipeline import create_ticket_intent_from_user_input
from utilities.exceptions import SlackUnknownCommandError

log_handler = logger.get_logger(__name__)


# Registry of Slack commands and their corresponding handlers
slack_command_registry: dict[
    models.SlackRequestType,
    Callable[
        [models.NormalizedSlackCommandRequest],
        models.SlackResponsePayload]
    ] = {}


def slack_command(command: models.SlackRequestType):
    """
    Decorator to register a function as a
    handler for a specific Slack command.
    """
    def decorator(func: Callable):
        slack_command_registry[command] = func
        return func
    return decorator


@slack_command(models.SlackRequestType.CREATE_TICKET)
async def handle_create_ticket(
    slack_request: models.NormalizedSlackCommandRequest
) -> models.SlackResponsePayload:
    """
    Handler for processing Slack ticket creation requests
    """
    # Process the user input and create a structured ticket intent
    ticket_intent = create_ticket_intent_from_user_input(
        slack_request.text
    )
    # Build a Slack message with the ticket intent
    # and return it as a Slack response
    slack_text_body = ticket_intent.to_string()
    log_handler.info(
        f"\nGenerated Slack response text: \n{slack_text_body}"
    )
    slack_message = models.SlackMessage(
        text=slack_text_body,
    )
    return slack_message.to_slack_response()


async def slack_intent_handler(
    slack_command_request: models.NormalizedSlackCommandRequest
) -> None:
    """
    Handler for routing Slack commands to the appropriate function.
    """
    request_handler = slack_command_registry.get(
        slack_command_request.intent
    )
    if not request_handler:
        raise SlackUnknownCommandError(
            f"No handler defined for command: "
            f"{slack_command_request.intent}"
        )
    slack_response = await request_handler(slack_command_request)
    if slack_command_request.response_url:
        await client.send_response_to_slack(
            slack_command_request.response_url,
            slack_response
        )
