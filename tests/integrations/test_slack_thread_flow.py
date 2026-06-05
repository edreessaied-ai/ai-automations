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


def test_draft_preview_blocks_contain_all_actions() -> None:
    built = blocks.build_draft_preview_blocks(_sample_intent(), "draft-1")
    actions = [b for b in built if b["type"] == "actions"]
    assert len(actions) == 1

    elements = actions[0]["elements"]
    action_ids = {el["action_id"] for el in elements}
    assert action_ids == {
        "confirm_ticket",
        "improve_ticket",
        "edit_ticket",
        "cancel_ticket",
    }
    # Each button carries the draft id so the click can recover the draft.
    assert all(el["value"] == "draft-1" for el in elements)


# ---------------------------------------------------------------------------
# Refinement loop: draft store peek/update, edit modal, view submission
# ---------------------------------------------------------------------------


def test_draft_store_get_and_update_preserve_draft() -> None:
    record = draft_store.save_draft(_sample_intent(), "C1", "1.0")
    # Peeking does not consume the draft.
    assert draft_store.get_draft(record.draft_id) is not None
    assert draft_store.get_draft(record.draft_id) is not None

    revised = _sample_intent()
    revised.title = "Revised title"
    updated = draft_store.update_draft(record.draft_id, revised)
    assert updated is not None
    assert updated.draft_id == record.draft_id
    refreshed = draft_store.get_draft(record.draft_id)
    assert refreshed is not None
    assert refreshed.intent.title == "Revised title"


def test_update_draft_missing_returns_none() -> None:
    assert draft_store.update_draft("does-not-exist", _sample_intent()) is None


def test_edit_modal_view_round_trips_draft_id() -> None:
    view = blocks.build_edit_modal_view("draft-77")
    assert view["callback_id"] == models.EDIT_MODAL_CALLBACK_ID
    assert view["private_metadata"] == "draft-77"
    assert view["blocks"][0]["block_id"] == models.EDIT_MODAL_BLOCK_ID


def test_parse_view_submission_extracts_instructions_and_draft_id() -> None:
    payload = {
        "type": "view_submission",
        "user": {"id": "U7"},
        "view": {
            "private_metadata": "draft-9",
            "state": {
                "values": {
                    models.EDIT_MODAL_BLOCK_ID: {
                        models.EDIT_MODAL_ACTION_ID: {
                            "type": "plain_text_input",
                            "value": "make it medium priority",
                        }
                    }
                }
            },
        },
    }
    submission = parser.parse_view_submission(payload)
    assert submission.draft_id == "draft-9"
    assert submission.instructions == "make it medium priority"
    assert submission.user_id == "U7"


def test_parse_interaction_payload_captures_trigger_id() -> None:
    action = parser.parse_interaction_payload(
        {
            "trigger_id": "trig-123",
            "actions": [{"action_id": "edit_ticket", "value": "draft-1"}],
        }
    )
    assert action.action is models.SlackActionType.EDIT_TICKET
    assert action.trigger_id == "trig-123"


def test_updated_draft_message_replace_original_flag() -> None:
    msg = blocks.build_updated_draft_message(
        _sample_intent(), "draft-1", replace_original=True
    )
    assert msg.to_slack_response()["replace_original"] is True
    # Without the flag, the payload omits replace_original entirely.
    msg2 = blocks.build_updated_draft_message(_sample_intent(), "draft-1")
    assert "replace_original" not in msg2.to_slack_response()
