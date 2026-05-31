"""
Tests for the Slack thread -> Jira ticket flow building blocks:
event parsing, thread-context cleaning, the draft store, and the
draft-preview Block Kit output.
"""
import integrations.slack.blocks as blocks
import integrations.slack.draft_store as draft_store
import integrations.slack.models as models
import integrations.slack.parser as parser
from domain.ticket.models import TicketIntent


def _sample_intent() -> TicketIntent:
    return TicketIntent(
        title="Payments API latency causing checkout failures",
        description="Elevated latency after the 2pm deploy.",
        priority="High",
        assignee=None,
        labels=["payments", "production"],
        summary="EU checkout failing due to payments API latency.",
    )


# ---------------------------------------------------------------------------
# Event / instruction parsing
# ---------------------------------------------------------------------------


def test_extract_user_instructions_strips_bot_mention() -> None:
    text = "<@U0BOT> create a high priority bug ticket"
    assert (
        parser.extract_user_instructions(text)
        == "create a high priority bug ticket"
    )


def test_extract_user_instructions_handles_plain_handle() -> None:
    text = "@TicketBot summarize this thread into an incident ticket"
    assert (
        parser.extract_user_instructions(text)
        == "summarize this thread into an incident ticket"
    )


def test_parse_app_mention_event() -> None:
    event = {
        "type": "app_mention",
        "channel": "C123",
        "user": "U42",
        "text": "<@U0BOT> create ticket",
        "thread_ts": "1717000000.123",
        "event_ts": "1717000000.999",
    }
    parsed = parser.parse_app_mention_event(event)
    assert parsed.channel_id == "C123"
    assert parsed.thread_ts == "1717000000.123"
    assert parsed.text == "<@U0BOT> create ticket"


def test_parse_app_mention_event_outside_thread_has_no_thread_ts() -> None:
    parsed = parser.parse_app_mention_event(
        {"channel": "C1", "text": "<@U0BOT> hi", "event_ts": "1.0"}
    )
    assert parsed.thread_ts is None


# ---------------------------------------------------------------------------
# Thread context cleaning
# ---------------------------------------------------------------------------


def test_clean_thread_to_text_normalizes_and_preserves_order() -> None:
    context = models.SlackThreadContext(
        channel_id="C1",
        thread_ts="1.0",
        messages=[
            models.SlackThreadMessage(
                user="alice", text="Hey <@U999>, see <http://x.com|the logs>",
                timestamp="1.0",
            ),
            models.SlackThreadMessage(
                user="bob", text="payments &amp; checkout broke",
                timestamp="2.0",
            ),
        ],
    )
    text = parser.clean_thread_to_text(context)
    lines = text.splitlines()
    assert lines[0] == "@alice: Hey @user, see the logs"
    assert lines[1] == "@bob: payments & checkout broke"


# ---------------------------------------------------------------------------
# Interaction payload parsing
# ---------------------------------------------------------------------------


def test_parse_interaction_payload_simulator_flat() -> None:
    action = parser.parse_interaction_payload(
        {"action": "confirm_ticket", "draft_id": "abc123"}
    )
    assert action.action is models.SlackActionType.CONFIRM_TICKET
    assert action.draft_id == "abc123"


def test_parse_interaction_payload_slack_nested() -> None:
    action = parser.parse_interaction_payload(
        {
            "user": {"id": "U7"},
            "response_url": "https://hooks.slack.com/actions/x",
            "actions": [
                {"action_id": "cancel_ticket", "value": "draft-9"}
            ],
        }
    )
    assert action.action is models.SlackActionType.CANCEL_TICKET
    assert action.draft_id == "draft-9"
    assert action.user_id == "U7"


# ---------------------------------------------------------------------------
# Draft store
# ---------------------------------------------------------------------------


def test_draft_store_round_trip_and_single_use() -> None:
    record = draft_store.save_draft(_sample_intent(), "C1", "1.0")
    popped = draft_store.pop_draft(record.draft_id)
    assert popped is not None
    assert popped.intent.title == _sample_intent().title
    # A draft can only be consumed once (prevents duplicate creation).
    assert draft_store.pop_draft(record.draft_id) is None


# ---------------------------------------------------------------------------
# Draft preview blocks
# ---------------------------------------------------------------------------


def test_draft_preview_blocks_contain_confirm_and_cancel() -> None:
    built = blocks.build_draft_preview_blocks(_sample_intent(), "draft-1")
    actions = [b for b in built if b["type"] == "actions"]
    assert len(actions) == 1

    elements = actions[0]["elements"]
    action_ids = {el["action_id"] for el in elements}
    assert action_ids == {"confirm_ticket", "cancel_ticket"}
    # Each button carries the draft id so the click can recover the draft.
    assert all(el["value"] == "draft-1" for el in elements)
