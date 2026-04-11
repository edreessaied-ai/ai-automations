"""
JiraService

Handles all interactions with Jira, including creating tickets.

This service is responsible for:
- Translating internal Ticket objects into Jira API payloads
- Sending requests to Jira
- Returning structured results (ID, URL)

This layer isolates external system logic
from the rest of the application.
"""

import requests

from utilities.constants import JIRA_TRANSACTION_TIMEOUT
from utilities.retry_util import retry
from utilities.ticket_util import Ticket
from utilities.type_util import EmailStr, TokenStr, URLStr


class JiraService:
    """
    Service for interacting with Jira API.
    """

    def __init__(
        self,
        base_url: URLStr,
        email: EmailStr,
        api_token: TokenStr,
    ) -> None:
        """
        Initialize JiraService.

        Args:
            base_url: Jira instance URL (e.g. https://your-domain.atlassian.net)
            email: Jira account email
            api_token: Jira API token
        """

        self.base_url = base_url
        self.email = email
        self.api_token = api_token

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError(
                "Missing Jira configuration (URL, email, or API token)"
            )

    # =========================================================
    # Public API
    # =========================================================

    def create_ticket(
        self, ticket: Ticket, project_key: str
    ) -> tuple[str, str]:
        """
        Create a Jira issue from a Ticket.

        Args:
            ticket: Internal Ticket object
            project_key: Jira project key (e.g. "ENG", "PROD")

        Returns:
            Tuple of (jira_issue_key, jira_issue_url)
        """

        url = f"{self.base_url}/rest/api/3/issue"

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": ticket.title,
                "description": self._format_description(ticket),
                "issuetype": {"name": "Task"},  # can be made configurable
                "priority": {"name": ticket.priority},
                "labels": ticket.labels,
            }
        }

        response = retry(
            requests.post,
            url,
            json=payload,
            auth=(self.email, self.api_token),
            headers={"Accept": "application/json"},
            timeout=JIRA_TRANSACTION_TIMEOUT,
        )

        if response.status_code != 201:
            raise RuntimeError(
                f"Failed to create Jira ticket: "
                f"{response.status_code} {response.text}"
            )

        data = response.json()

        issue_key = data["key"]
        issue_url = f"{self.base_url}/browse/{issue_key}"

        return issue_key, issue_url

    # =========================================================
    # Helpers
    # =========================================================

    def _format_description(self, ticket: Ticket) -> str:
        """
        Format ticket description for Jira.

        Jira Cloud expects Atlassian Document Format (ADF) for rich text,
        but for MVP we send plain text.

        Later upgrade:
        - Convert to ADF JSON
        - Add sections (Context, Impact, Steps)

        Args:
            ticket: Ticket object

        Returns:
            Formatted description string
        """
        return ticket.description
