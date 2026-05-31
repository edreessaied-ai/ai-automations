"""
    Slack command dispatcher for processing incoming Slack commands.
"""
import asyncio
from collections.abc import Awaitable, Callable

import integrations.slack.blocks as blocks
import integrations.slack.client as client
import integrations.slack.draft_store as draft_store
import integrations.slack.models as models
import integrations.slack.parser as parser
import utilities.exceptions as exceptions
import utilities.logger as logger
from api.services.jira_service import (
    JiraService,
    load_jira_api_token,
    load_jira_url,
    load_jira_user_email,
)
from domain.ticket.pipeline import (
    create_ticket_intent_from_thread,
    create_ticket_intent_from_user_input,
)
from integrations.jira.models import JIRA_PROJECT

log_handler = logger.get_logger(__name__)


# Slack command handlers are async and return a Slack response payload.
SlackCommandHandler = Callable[
    [models.NormalizedSlackCommandRequest],
    Awaitable[models.SlackResponsePayload],
]

# Registry of Slack commands and their corresponding handlers
slack_command_registry: dict[
    models.SlackRequestType,
    SlackCommandHandler,
] = {}


def slack_command(
    command: models.SlackRequestType,
) -> Callable[[SlackCommandHandler], SlackCommandHandler]:
    """
    Decorator to register a function as a
    handler for a specific Slack command.
    """
    def decorator(func: SlackCommandHandler) -> SlackCommandHandler:
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
            slack_request.text or ""
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


def _build_jira_service() -> JiraService:
    """Construct a JiraService from environment configuration."""
    return JiraService(
        base_url=load_jira_url(),
        email=load_jira_user_email(),
        api_token=load_jira_api_token(),
        project_key=JIRA_PROJECT,
    )


async def handle_app_mention(event: models.AppMentionEvent) -> None:
    """
    Process an `@Bot` mention: fetch the thread, generate a ticket draft,
    and post a confirmation preview. This never creates a Jira ticket on its
    own — creation only happens after the user clicks "Create Ticket".
    """
    # MVP is strictly thread-scoped: a mention outside a thread is rejected.
    if not event.thread_ts:
        log_handler.info("App mention received outside a thread; instructing.")
        await client.post_message(
            event.channel_id,
            event.event_ts,
            blocks.build_error_message(blocks.OUTSIDE_THREAD_MESSAGE),
        )
        return

    log_handler.info(
        f"Handling app mention in channel={event.channel_id} "
        f"thread_ts={event.thread_ts}"
    )

    # Step 2/3 — retrieve and clean thread context.
    try:
        thread_context = await client.fetch_thread_replies(
            event.channel_id, event.thread_ts
        )
    except exceptions.SlackThreadContextError:
        log_handler.exception("Could not retrieve Slack thread context")
        await client.post_message(
            event.channel_id,
            event.thread_ts,
            blocks.build_error_message(blocks.OUTSIDE_THREAD_MESSAGE),
        )
        return

    thread_text = parser.clean_thread_to_text(thread_context)
    user_instructions = parser.extract_user_instructions(event.text)

    # Step 4 — generate the structured ticket draft.
    try:
        ticket_intent = await create_ticket_intent_from_thread(
            thread_text=thread_text,
            user_instructions=user_instructions,
        )
    except Exception:
        log_handler.exception("LLM failed to generate ticket from thread")
        await client.post_message(
            event.channel_id,
            event.thread_ts,
            blocks.build_error_message(blocks.LLM_FAILURE_MESSAGE),
        )
        return

    # Step 5 — stash the draft and post the confirmation preview.
    draft = draft_store.save_draft(
        intent=ticket_intent,
        channel_id=event.channel_id,
        thread_ts=event.thread_ts,
    )
    preview = models.SlackMessage(
        text="Here's a proposed Jira ticket from this thread.",
        blocks=blocks.build_draft_preview_blocks(
            ticket_intent, draft.draft_id
        ),
    )
    await client.post_message(event.channel_id, event.thread_ts, preview)


async def _deliver_interaction_response(
    action: models.SlackInteractionAction,
    channel_id: str,
    thread_ts: str,
    message: models.SlackMessage,
) -> None:
    """
    Send a response to an interaction, preferring the payload's response_url
    (always provided by Slack) and falling back to chat.postMessage / the
    local sink otherwise.
    """
    if action.response_url:
        await client.send_response_to_slack(
            str(action.response_url), message.to_slack_response()
        )
        return
    await client.post_message(channel_id, thread_ts, message)


async def handle_interaction(action: models.SlackInteractionAction) -> None:
    """
    Process a draft confirmation button click (Create Ticket / Cancel).
    """
    log_handler.info(
        f"Handling interaction action={action.action} "
        f"draft_id={action.draft_id}"
    )
    draft = draft_store.pop_draft(action.draft_id)
    if draft is None:
        log_handler.warning(f"Draft {action.draft_id} not found or expired.")
        await _deliver_interaction_response(
            action,
            channel_id="",
            thread_ts="",
            message=blocks.build_error_message(blocks.DRAFT_EXPIRED_MESSAGE),
        )
        return

    if action.action is models.SlackActionType.CANCEL_TICKET:
        await _deliver_interaction_response(
            action,
            draft.channel_id,
            draft.thread_ts,
            blocks.build_cancelled_message(),
        )
        return

    # Step 6 — create the Jira ticket after explicit confirmation.
    try:
        jira_service = _build_jira_service()
        # create_ticket uses blocking I/O (requests); run it in a thread so
        # it doesn't block the event loop in this async background task.
        jira_instance = await asyncio.to_thread(
            jira_service.create_ticket, draft.intent
        )
    except Exception:
        log_handler.exception("Failed to create Jira ticket from draft")
        await _deliver_interaction_response(
            action,
            draft.channel_id,
            draft.thread_ts,
            blocks.build_error_message(blocks.JIRA_FAILURE_MESSAGE),
        )
        return

    await _deliver_interaction_response(
        action,
        draft.channel_id,
        draft.thread_ts,
        blocks.build_creation_success_message(jira_instance),
    )


async def slack_intent_handler(
    slack_command_request: models.NormalizedSlackCommandRequest
) -> None:
    """
    Handler for routing Slack commands to the appropriate function.
    """
    log_handler.info(
        f"Starting BG Slack Intent Handler for {slack_command_request.intent}"
    )
    intent = slack_command_request.intent
    request_handler = (
        slack_command_registry.get(intent) if intent is not None else None
    )
    if not request_handler:
        raise exceptions.SlackUnknownCommandError(
            f"No handler defined for command: "
            f"{slack_command_request.intent}"
        )
    slack_response = await request_handler(slack_command_request)
    if slack_command_request.response_url:
        await client.send_response_to_slack(
            str(slack_command_request.response_url),
            slack_response
        )
    log_handler.info(
        f"Completed BG Slack Intent Handler for {slack_command_request.intent}"
    )
