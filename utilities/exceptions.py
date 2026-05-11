"""
    Custom exceptions.
"""


class SlackUnknownCommandError(Exception):
    """Exception raised when an unknown Slack command is received."""


class DataTransformationError(Exception):
    """Exception raised when there is an error in data transformation."""


class SlackResponseSendError(Exception):
    """Raised when sending a response to Slack fails."""
