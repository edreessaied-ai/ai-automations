"""
    Slack command dispatcher for processing incoming Slack commands.
"""
import asyncio
from collections.abc import Callable

import integrations.slack.client as client
import integrations.slack.models as models
import utilities.exceptions as exceptions
import utilities.logger as logger
from api.services.jira_service import (
    JiraService,
    load_jira_api_token,
    load_jira_url,
    load_jira_user_email,
)
from domain.ticket.pipeline import create_ticket_intent_from_user_input
from integrations.jira.models import JIRA_PROJECT

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
    log_handler.info(
        "Creating ticket in JIRA based on Slack command..."
    )
    try:
        # Process the user input and create a structured ticket intent
        ticket_intent = await create_ticket_intent_from_user_input(
            slack_request.text
        )
        jira_service = JiraService(
            base_url=load_jira_url(),
            email=load_jira_user_email(),
            api_token=load_jira_api_token(),
            project_key=JIRA_PROJECT
        )
        # create_ticket uses blocking I/O (requests); run it in a thread
        # so it doesn't block the event loop in this async background task.
        jira_instance = await asyncio.to_thread(
            jira_service.create_ticket, ticket_intent
        )
    except Exception:
        # This handler runs in a fire-and-forget background task, so an
        # uncaught error would leave the user with only the initial ack.
        log_handler.exception(
            "Failed to create Jira ticket from Slack command"
        )
        error_message = models.SlackMessage(
            text=(
                ":warning: Sorry, I couldn't create your ticket. "
                "Please try again in a moment."
            ),
        )
        return error_message.to_slack_response()

    slack_response_string = (
        f"Ticket created successfully in JIRA: "
        f"{jira_instance.issue_key}, {jira_instance.issue_url}"
        f"\n{ticket_intent.to_string()}"
    )
    log_handler.info(
        f"\nGenerated Slack response text: \n{slack_response_string}"
    )
    slack_message = models.SlackMessage(
        text=slack_response_string,
    )
    return slack_message.to_slack_response()


async def slack_intent_handler(
    slack_command_request: models.NormalizedSlackCommandRequest
) -> None:
    """
    Handler for routing Slack commands to the appropriate function.
    """
    log_handler.info(
        f"Starting BG Slack Intent Handler for {slack_command_request.intent}"
    )
    request_handler = slack_command_registry.get(
        slack_command_request.intent
    )
    if not request_handler:
        raise exceptions.SlackUnknownCommandError(
            f"No handler defined for command: "
            f"{slack_command_request.intent}"
        )
    slack_response = await request_handler(slack_command_request)
    if slack_command_request.response_url:
        await client.send_response_to_slack(
            slack_command_request.response_url,
            slack_response
        )
    log_handler.info(
        f"Completed BG Slack Intent Handler for {slack_command_request.intent}"
    )
