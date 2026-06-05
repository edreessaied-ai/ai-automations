# AI Ticket Assistant

A Slack-native AI agent that turns unstructured conversations into high-quality,
structured Jira tickets — without leaving Slack.

Mention the bot in a thread and it reads the discussion, drafts a well-formed
ticket, and posts a preview with **Improve**, **Edit**, **Create**, and
**Cancel** controls. Nothing is written to Jira until a human explicitly
confirms.

```
@TicketBot  →  AI drafts a ticket  →  Improve / Edit in Slack  →  Create  →  Jira issue
```

---

## Why

Teams lose time on poorly written, incomplete, or missing tickets, and context
from Slack discussions rarely makes it into the tracker. This assistant acts as
a lightweight "front desk" for ticket creation: it captures the conversation,
structures it, and keeps a human in the loop for the final call.

The full product thinking lives in [`DESIGNDOC.md`](./DESIGNDOC.md).

---

## How it works

```
Slack thread
   │  @mention (app_mention event)
   ▼
FastAPI  ──►  thread context fetched (conversations.replies)
   │
   ▼
LLM pipeline  ──►  structured TicketIntent (title, description, priority, labels, summary)
   │
   ▼
Block Kit draft preview  ──►  [ Create | 🔄 Improve | ✏️ Edit | Cancel ]
   │                               │              │
   │                       regenerate in     modal: natural-language
   │                       place (improve)    edit instruction
   ▼
Create  ──►  Jira REST API  ──►  issue created, link returned
```

- **Thread-scoped:** the bot only reasons over the thread it's mentioned in.
- **Human-in-the-loop:** a Jira ticket is only created after an explicit
  **Create** click.
- **Iterative:** **Improve** and **Edit** refine the draft as many times as
  needed; the draft survives until you Create or Cancel.

---

## Tech stack

- **Python 3.12**, **FastAPI** (async background tasks for fast Slack acks)
- **OpenAI** for structured ticket extraction (JSON-schema constrained output)
- **Slack** Events / Interactivity / Slash Command APIs + Block Kit
- **Jira** REST API
- **Pydantic** for strict validation of AI-generated data
- **pytest**, **ruff**, **mypy (strict)** for quality

---

## Project structure

```
api/                  FastAPI app, routers, services, middleware
  main.py             App entrypoint + local simulator UI
  routers/slack.py    Slack events / interactions / commands endpoints
  services/           Jira service
domain/ticket/        Core ticket logic
  pipeline.py         LLM prompts + generate / improve / edit functions
  models.py           TicketIntent and related models
integrations/
  slack/              Slack client, dispatcher, parser, blocks, security, drafts
  jira/               Jira payload mapping + models
  llm/                OpenAI client
utilities/            Logging, exceptions, shared types/constants
templates/            Local Slack simulator UI (index.html)
tests/                pytest suite
DEMO_RUNBOOK.md       Live-demo rehearsal checklist
DESIGNDOC.md          Product & UX design document
```

---

## Getting started

### 1. Install

```bash
python3.12 -m venv ai-tools-venv
source ai-tools-venv/bin/activate
pip install -e .
```

### 2. Configure

Create a `.env` file in the repo root:

```bash
OPENAI_API_KEY="sk-..."
JIRA_API_TOKEN="..."
JIRA_URL="https://your-domain.atlassian.net/"
JIRA_USER_EMAIL="you@example.com"
JIRA_PROJECT_KEY="AIDEMO"          # target Jira project

# Required for real Slack; leave empty to use the local simulator
SLACK_BOT_TOKEN="xoxb-..."
SLACK_SIGNING_SECRET=""            # verifies inbound Slack requests when set
```

### 3. Run

```bash
uvicorn api.main:app --port 8000
```

- App: `http://localhost:8000`
- Health check: `http://localhost:8000/health`

---

## Two ways to run it

### Local simulator (no Slack workspace needed)

When `SLACK_BOT_TOKEN` is **unset**, the bot transparently falls back to an
in-memory store and serves a browser-based Slack simulator at
`http://localhost:8000/`. This lets you exercise the full
generate → refine → confirm → create flow without a real workspace.

### Against a real Slack workspace

1. Expose your local server over HTTPS (e.g. `ngrok http 8000`).
2. In your Slack app config, point all three URLs at the tunnel:
   - **Event Subscriptions** → `https://<tunnel>/slack/events`, subscribe to the
     `app_mention` bot event
   - **Interactivity & Shortcuts** → `https://<tunnel>/slack/interactions`
     (powers the buttons and the Edit modal)
   - **Slash Commands** (optional) → `/ticket` → `https://<tunnel>/slack/commands`
3. Add bot scopes: `app_mentions:read`, `chat:write`, `channels:history`,
   `groups:history`, `im:history`, `mpim:history`, `commands`. Reinstall the app.
4. Invite the bot to a channel: `/invite @TicketBot`.
5. Set `SLACK_SIGNING_SECRET` (from the app's Basic Information page) so inbound
   requests are verified.

> Presenting this to someone? See [`DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md) for a
> full rehearsal and live-demo checklist.

---

## Security

When `SLACK_SIGNING_SECRET` is set, every inbound Slack request
(events, interactions, slash commands) is verified against Slack's
HMAC-SHA256 signature, with a timestamp check to blunt replay attacks
(`integrations/slack/security.py`). Leaving the secret empty disables the check
and is intended only for local development / the simulator.

---

## Development

```bash
pytest            # run the test suite
ruff check .      # lint
mypy .            # strict type checking
```

Config for all three lives in `pyproject.toml` (ruff line length 80, mypy
strict, pydantic plugin enabled).
