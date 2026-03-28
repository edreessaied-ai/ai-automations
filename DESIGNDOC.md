AI Ticket Assistant – Product & UX Design Document (MVP)

1. Overview
The AI Ticket Assistant is a Slack-native AI agent that converts unstructured user input into high-quality, structured Jira tickets. It acts as a lightweight “front desk” for engineering teams, reducing friction in ticket creation and improving ticket clarity and consistency.
The MVP focuses on a single core workflow:
Generate → Refine → Confirm → Create ticket, all within Slack.

2. Problem Statement
Teams using Jira often encounter:
Poorly written or incomplete tickets
Time wasted clarifying issues
Friction in creating tickets
Loss of context from conversations
This leads to inefficiency and slower execution.

3. Goals and Non-Goals
Goals
Create tickets in <30 seconds
Improve ticket quality and structure
Minimize user effort via natural language
Keep all interactions within Slack
Require minimal setup (<10 minutes)
Non-Goals (MVP)
Multi-platform ticketing (Zendesk, ServiceNow)
Advanced workflow automation
Complex UI dashboards
Autonomous ticket creation without confirmation

4. Target Users
Software engineers
Tech leads
Internal teams reporting issues
Environment:
Heavy Slack usage
Jira for issue tracking

5. Core Workflow
Primary Flow
User runs Slack command: /ticket <message>
AI generates structured ticket draft
User iterates via:
Improve (AI refinement)
Edit (natural language instruction)
User confirms → ticket is created in Jira

6. Core Features
6.1 Create Ticket (Primary Feature)
Command:
/ticket <freeform text>

Input Examples:
“login is broken after password reset”
“payments failing for EU users after deploy”
AI Output:
Title
Description
Priority
Labels (optional)

6.2 Improve Ticket (Inline Action)
Not a primary command—available as a button in the flow.
Behavior:
Takes current draft
Enhances clarity, structure, completeness

6.3 Edit Ticket (Natural Language)
Triggered via button
User provides instruction:
make it medium priority and mention mobile impact

System:
Applies instruction to current draft
Returns updated ticket

6.4 Summarize Thread (Secondary Feature)
Command:
/summarize-thread

Behavior:
Reads Slack thread
Generates structured ticket

7. User Experience Design
7.1 Draft Display (Slack)
Ticket drafts are shown as a structured Slack Block Kit message, not raw text.

Example Draft UI
🧾 Ticket Draft
Title
Payment failures for EU users after deploy
Description
Users in the EU are experiencing payment failures following the latest deployment. The issue appears intermittent.
Priority
High

Buttons:
✅ Create Ticket
✏️ Edit
🔄 Improve

7.2 Interaction Model
Drafts appear as ephemeral messages (private to user)
All updates modify the same message
No new messages per iteration

7.3 Editing Flow
User clicks Edit
Prompt appears: What would you like to change?
User responds with natural language
AI updates draft

7.4 Improvement Flow
User clicks Improve
AI refines current draft
Message updates in place

8. Input Handling
System accepts any text format:
Structured Input
Title: Login issue
Description: Users cannot log in...
Priority: Medium

Semi-structured
Login issue

Users cannot log in after password reset

Unstructured
login broken after reset

System Behavior:
Detect structure if present
Infer structure if missing

9. System Architecture
Components
Slack Interface
Slash commands
Interactive buttons
Backend
FastAPI
Handles routing and orchestration
AI Layer
Generates structured output
Handles edits and improvements
Jira Integration
Creates tickets via REST API

Data Flow
Slack command received
Backend processes request
AI generates structured ticket
Draft displayed in Slack
User interacts (edit/improve)
Final confirmation → Jira API call
Ticket created

10. Data Model (Simplified)
{
  "user_id": "...",
  "channel_id": "...",
  "message_ts": "...",
  "original_input": "...",
  "current_draft": {
    "title": "...",
    "description": "...",
    "priority": "High",
    "labels": []
  }
}


11. AI Behavior Specification
Capabilities
Interpret vague input
Infer missing structure
Generate concise, actionable tickets
Apply reasonable defaults
Constraints
Avoid verbosity
Avoid unnecessary follow-ups
Always return structured output

12. Setup Experience
Required
Jira API token
Project key
Automated
Fetch fields and issue types
Optional prompts
Default priority mapping
Default issue type

13. Success Metrics
Efficiency
Ticket creation time <30 seconds
Quality
<30% user edits
Adoption
Repeat usage within days
Command frequency

14. Risks and Mitigations
Low AI quality
Improve prompts
Use examples
Jira variability
Start with minimal required fields
User trust
Always show preview
Allow easy edits

15. Future Enhancements
Ticket ID support for /improve-ticket
Multi-platform integrations
Learning from user edits
Admin configuration UI (web interface)
Passive suggestions in Slack

16. Strategic Principles
Prioritize one excellent interface (Slack)
Optimize for speed and simplicity
Treat drafts as conversation state, not documents
Focus on output quality over feature breadth

17. Steps to Completion
Step 1 — AI Layer (START HERE)
Build a simple script:
input = "payments failing for EU users after deploy"

output = generate_ticket(input)

print(output)
Focus on:
Prompt quality
Output structure
Consistency
Test with:
messy input
structured input
edge cases
👉 Iterate until outputs are consistently good
Step 2 — Backend (thin wrapper)
Wrap your AI in FastAPI:
/generate-ticket
/improve-ticket
/edit-ticket
Still no Slack. No Jira.
Just:
input → output
Step 3 — Jira Integration
Now connect:
Take AI output
Create real ticket via API
Handle:
required fields
formatting
Step 4 — Slack Interface (LAST)
Only now add:
/ticket
buttons (Improve, Edit, Create)
Because now:
your AI works
your backend works
your Jira integration works
Slack becomes just a UI layer.

17. Conclusion
The AI Ticket Assistant MVP is a focused, high-impact solution to improve how teams create and manage tickets. By embedding directly into Slack and leveraging AI for structured output, it minimizes friction while maximizing clarity and efficiency.
The success of the product depends on delivering:
fast interactions
high-quality outputs
seamless user experience
This MVP establishes a strong foundation for future expansion into a broader AI-powered workflow assistant.


