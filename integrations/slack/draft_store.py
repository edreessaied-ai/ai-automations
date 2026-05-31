"""
In-memory store for pending ticket drafts awaiting user confirmation.

When the bot posts a draft preview it stashes the generated ticket here,
keyed by a freshly minted draft id that is embedded in the Create/Cancel
buttons. The interaction handler later pops the draft back out to create the
Jira ticket. This keeps the confirmation step stateless from Slack's side.

This is process-local memory, which is sufficient for the MVP. A persistent
store (or short-TTL cache) would be the natural next step for production.
"""
import uuid
from dataclasses import dataclass

from domain.ticket.models import TicketIntent


@dataclass
class TicketDraftRecord:
    """A pending ticket draft tied to the thread it was generated from."""
    draft_id: str
    intent: TicketIntent
    channel_id: str
    thread_ts: str


_DRAFTS: dict[str, TicketDraftRecord] = {}


def save_draft(
    intent: TicketIntent,
    channel_id: str,
    thread_ts: str,
) -> TicketDraftRecord:
    """Store a draft and return its record (including a new draft id)."""
    draft_id = uuid.uuid4().hex
    record = TicketDraftRecord(
        draft_id=draft_id,
        intent=intent,
        channel_id=channel_id,
        thread_ts=thread_ts,
    )
    _DRAFTS[draft_id] = record
    return record


def pop_draft(draft_id: str) -> TicketDraftRecord | None:
    """
    Remove and return a draft by id.

    Popping (rather than reading) ensures a draft can only be acted on once,
    preventing duplicate ticket creation from repeated button clicks.
    """
    return _DRAFTS.pop(draft_id, None)
