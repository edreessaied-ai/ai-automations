"""
Local development sink for the Slack -> Jira flow.

Real Slack delivers thread context via `conversations.replies` and receives
bot replies via `chat.postMessage`. When no `SLACK_BOT_TOKEN` is configured
(local development / the bundled Slack simulator), there is no workspace to
call, so we fall back to this in-memory store:

- `seed_thread` / `get_seeded_thread` stand in for `conversations.replies`,
  letting the simulator pre-load a thread the bot can "read".
- `publish_message` / `get_latest_message` stand in for `chat.postMessage`,
  capturing the bot's reply so the simulator UI can render it.

This module holds process-local state only and is intended for local use.
"""
from typing import Any

import integrations.slack.models as models

# Seeded threads keyed by (channel_id, thread_ts), simulating Slack history.
_SEEDED_THREADS: dict[tuple[str, str], models.SlackThreadContext] = {}

# The most recent message the bot "posted", for the simulator to poll.
_LATEST_MESSAGE: dict[str, Any] = {}


def _thread_key(channel_id: str, thread_ts: str) -> tuple[str, str]:
    """Build the lookup key for a seeded thread."""
    return (channel_id, thread_ts)


def seed_thread(context: models.SlackThreadContext) -> None:
    """
    Store a thread so the local `fetch_thread_replies` fallback can read it.
    """
    key = _thread_key(context.channel_id, context.thread_ts)
    _SEEDED_THREADS[key] = context


def get_seeded_thread(
    channel_id: str,
    thread_ts: str,
) -> models.SlackThreadContext | None:
    """Retrieve a previously seeded thread, if any."""
    return _SEEDED_THREADS.get(_thread_key(channel_id, thread_ts))


def publish_message(payload: dict[str, Any]) -> None:
    """Capture a bot reply for the simulator to display."""
    _LATEST_MESSAGE.clear()
    _LATEST_MESSAGE.update(payload)


def get_latest_message() -> dict[str, Any]:
    """Return the most recently captured bot reply."""
    return dict(_LATEST_MESSAGE)
