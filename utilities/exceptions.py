"""
    Custom exceptions.
"""


class SlackUnknownCommandError(Exception):
    """Exception raised when an unknown Slack command is received."""


class DataTransformationError(Exception):
    """Exception raised when there is an error in data transformation."""


class SlackResponseSendError(Exception):
    """Raised when sending a response to Slack fails."""


class JiraConfigurationError(Exception):
    """Raised when required Jira configuration is missing."""


class SlackConfigurationError(Exception):
    """Raised when required Slack configuration is missing."""


class SlackThreadContextError(Exception):
    """Raised when a Slack thread cannot be retrieved or is empty."""


class LLMTicketGenerationError(Exception):
    """Raised when the LLM cannot confidently generate a ticket."""
