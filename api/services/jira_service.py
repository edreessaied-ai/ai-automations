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
import os

import requests

from domain.ticket.models import TicketIntent
from integrations.jira.mapper import intent_to_jira_payload
from integrations.jira.models import JIRA_TRANSACTION_TIMEOUT, JiraInstance
from utilities.logger import get_logger
from utilities.retry_util import RetryException, retry
from utilities.types import EmailStr, TokenStr, URLStr

log_handler = get_logger(__name__)


def load_jira_user_email() -> str | None:
    """
    Load the JIRA user email.
    """
    jira_user_email = os.getenv("JIRA_USER_EMAIL")
    if not jira_user_email:
        log_handler.error(
            "JIRA user email not found in environment variables."
        )
    return jira_user_email


def load_jira_api_token() -> str | None:
    """
    Load the JIRA API token.
    """
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    if not jira_api_token:
        log_handler.error(
            "JIRA API token not found in environment variables."
        )
    return jira_api_token


def load_jira_url() -> str | None:
    """
    Load the JIRA URL.
    """
    jira_url = os.getenv("JIRA_URL")
    if not jira_url:
        log_handler.error(
            "JIRA URL not found in environment variables."
        )
    return jira_url


class JiraService:
    """
    Service for interacting with Jira.
    """
    def __init__(
        self,
        base_url: URLStr,
        email: EmailStr,
        api_token: TokenStr,
        project_key: str,
    ) -> None:
        """
        Initialize JiraService.

        Args:
            base_url: Jira instance URL
            (e.g. https://your-domain.atlassian.net)
            email: Jira account email
            api_token: Jira API token
        """
        self.base_url = base_url
        self.email = email
        self.api_token = api_token
        self.project_key = project_key

    def create_ticket(
        self, ticket_intent: TicketIntent,
    ) -> JiraInstance:
        """
        Create a Jira issue from a Ticket.

        Args:
            ticket: Internal Ticket object
            project_key: Jira project key (e.g. "ENG", "PROD")

        Returns:
            Tuple of (jira_issue_key, jira_issue_url)
        """
        log_handler.info(
            f"Creating Jira ticket for intent: \n{ticket_intent.to_string()}"
        )
        # Transform the internal TicketIntent into a Jira-compatible format
        jira_payload = intent_to_jira_payload(ticket_intent=ticket_intent)

        url = f"{self.base_url}/rest/api/3/issue"
        try:
            response = retry(
                requests.post,
                url=url,
                json=jira_payload,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"},
                timeout=JIRA_TRANSACTION_TIMEOUT,
            )
        except RetryException as exc:
            log_handler.error(
                f"Error occurred while creating Jira ticket: {exc}"
            )
            raise RuntimeError(
                f"Failed to create Jira ticket: {exc}"
            ) from exc

        if response.status_code != 201:
            raise RuntimeError(
                f"Failed to create Jira ticket: "
                f"{response.status_code} {response.text}"
            )
        data = response.json()
        issue_key = data["key"]
        issue_url = f"{self.base_url}/browse/{issue_key}"

        # Return a structured JiraInstance
        jira_instance = JiraInstance(
            issue_key=issue_key,
            issue_url=issue_url,
        )
        log_handler.info(f"Created Jira issue {issue_key} at {issue_url}")
        return jira_instance
