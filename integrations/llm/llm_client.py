"""
    LLMClient: A client for interacting with
    Large Language Models (LLMs) to extract structured data.
"""

import os
from typing import Protocol, TypeVar

from openai import OpenAI
from pydantic import BaseModel

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    """
    Protocol for LLM clients that can
    extract structured data from prompts.
    """
    def extract_structured(
        self,
        prompt: str,
        system_prompt: str,
        data_model: type[T],
        max_retries: int = 3,
    ) -> T:
        """
        Extract structured data from the LLM
        response, with retries.
        """
