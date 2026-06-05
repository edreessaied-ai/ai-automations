# Demo Runbook — AI Ticket Assistant (Slack → Jira)

A rehearsal and live-demo checklist for presenting the bot against a real Slack
workspace. Split into: **prep → dry run → live flow → failure recovery →
go/no-go**.

---

## 1. Pre-demo setup (day before *and* re-verify ~30 min before)

### Environment (`.env`) — all six must be set
- [ ] `OPENAI_API_KEY` — has quota/credits (a dead key = silent draft failures)
- [ ] `JIRA_API_TOKEN`, `JIRA_URL`, `JIRA_USER_EMAIL`
- [ ] `JIRA_PROJECT_KEY` → your **clean demo project** (not dev clutter)
- [ ] `SLACK_BOT_TOKEN` (`xoxb-…`)
- [ ] `SLACK_SIGNING_SECRET` — ⚠️ a **wrong** value makes *every* Slack request
      401 silently and the bot just does nothing. Confirm it matches
      Slack → Basic Information.

### Slack app config — all three URLs point at the *current* tunnel host
- [ ] Event Subscriptions → `https://<tunnel>/slack/events` + subscribed to the
      **`app_mention`** bot event
- [ ] Interactivity → `https://<tunnel>/slack/interactions` (powers buttons
      **and** the Edit modal)
- [ ] Slash Commands → `/ticket` → `https://<tunnel>/slack/commands`
      (only if demoing the slash command)

### Scopes installed (reinstall if changed)
`app_mentions:read`, `chat:write`, `channels:history`, `groups:history`,
`im:history`, `mpim:history`, `commands`

### Workspace
- [ ] Bot is **invited** to the demo channel (`/invite @TicketBot`)
- [ ] Clean demo channel, no clutter
- [ ] Machine clock is correct (the signature check rejects requests with
      >5 min clock skew)

---

## 2. Solo dry run (full rehearsal, ~1 hr before)

1. [ ] Start the server: `uvicorn api.main:app --port 8000`
2. [ ] Start the tunnel and **leave it running** — note the URL
3. [ ] Health check: `curl https://<tunnel>/health` → `{"status":"Healthy"}`
4. [ ] Post a realistic seed thread (2–4 messages, e.g. a payments/login
       incident), then in a **reply** type `@TicketBot create a ticket`
5. [ ] Verify the **draft preview** appears with all four buttons:
       Create · 🔄 Improve · ✏️ Edit · Cancel
6. [ ] Click **🔄 Improve** → draft updates **in place**
7. [ ] Click **✏️ Edit** → modal opens → type
       *"make it high priority and mention mobile impact"* → Apply →
       updated draft posts back
8. [ ] Click **Create Ticket** → success message with Jira key/URL →
       **open the link** and confirm the ticket exists with correct
       priority/labels in the demo project
9. [ ] Watch server logs throughout — confirm `POST /slack/events` and
       `/slack/interactions` arrive with no 401s or tracebacks

> ⚠️ **Critical:** After the dry run passes, **do not restart the server**
> before the demo — drafts live in memory (`draft_store.py`); a restart wipes
> pending drafts ("draft expired"). Don't restart the tunnel either; a new URL
> silently breaks all three Slack endpoints.

---

## 3. Live demo flow (the narrative)

Have a **pre-written seed thread** ready to paste so you're not improvising
prose live:

1. Paste the seed thread (a messy, realistic discussion)
2. `@TicketBot` it → *"Notice it read the whole thread and structured it"*
3. Click **Improve** → *"One click to tighten it up"*
4. Click **Edit**, type a change → *"Or steer it in plain English"*
   (strongest moment — lead with it if time is short)
5. Click **Create** → open the Jira ticket → *"Real ticket, ~20 seconds, you
   stayed in control the whole time"*

Rehearse the LLM pauses (a few seconds each) so silence doesn't feel like a
freeze — narrate while it thinks.

---

## 4. Failure modes & quick recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| Bot ignores the mention entirely | Tunnel URL changed / not subscribed to `app_mention` / wrong signing secret (401s) | Check logs for incoming POST; if none, re-check Events URL + signing secret |
| Buttons do nothing | Interactivity URL unset/stale | Re-point Interactivity to current tunnel |
| Edit modal won't open | Trigger expired or Interactivity misconfigured | Re-click Edit; verify Interactivity URL |
| "Draft expired" on Create | Server restarted mid-demo | Re-mention to generate a fresh draft |
| Draft generation fails | OpenAI key/quota | Have a backup key ready |
| Everything 401s silently | Wrong `SLACK_SIGNING_SECRET` or clock skew | Fix secret / sync clock; last resort: blank the secret to disable verification |

**Universal recovery move:** if a single draft gets weird, just `@TicketBot`
again in the thread for a fresh one.

---

## 5. Final go/no-go (5 min before)
- [ ] `curl /health` returns healthy
- [ ] One full real run completed today on the current tunnel
      (mention → improve → edit → create → Jira link opens)
- [ ] Server + tunnel have **not** been restarted since that run
- [ ] Seed thread text is on your clipboard
- [ ] Backup: a screen recording of the working flow, in case live
      connectivity fails
