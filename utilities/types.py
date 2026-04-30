"""
Type Utility Module

This modules defines a set of useful types that can be used
across the codebase to improve readability, maintainability,
and type safety.
"""

from typing import Any

JSONStr = str
ErrStr = str

type Json = dict[str, Any]

AIResponse = object

JsonSchema = dict[str, object]


URLStr = str
EmailStr = str
TokenStr = str

# Slack specific types
SlackTimestampStr = str
SlackChannelIDStr = str
SlackUserIDStr = str
SlackInputTextStr = str

# LLM response types
JsonLLMResponse = str
