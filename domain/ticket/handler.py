"""
Ticket handlers for processing ticket-related operations.
"""
import integrations.slack.models as models
import utilities.logger as logger
from domain.ticket.pipeline import send_ticket_request_to_llm

log_handler = logger.get_logger(__name__)


async def ticket_creation_handler_for_slack(
    slack_command_request: models.NormalizedSlackCommandRequest
) -> models.SlackResponsePayload:
    """
    Handler for ticket-related Slack commands.
    """
    # Send the user input to the LLM and get a structured ticket intent back
    ticket_intent = send_ticket_request_to_llm(
        user_prompt=slack_command_request.text,
    )

    # Log the structured ticket intent for debugging
    log_handler.info(ticket_intent)

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
