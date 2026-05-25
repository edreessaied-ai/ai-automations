"""
    JIRA integration module for JIRA-related python models/types.
"""
from dataclasses import dataclass

# Jira-related Constants
JIRA_PROJECT = "AIDEMO"
JIRA_TRANSACTION_TIMEOUT = 60  # seconds

# Types
JIRAProjectKey = str


@dataclass
class JiraInstance:
    """
    Represents a Jira instance with necessary credentials and configuration.
    """
    issue_key: str
    issue_url: str
