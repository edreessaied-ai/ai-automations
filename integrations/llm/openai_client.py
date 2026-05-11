"""
    This module defines a client for interacting
    with OpenAI's language models.
"""
import json
import os
from typing import TypeVar

from openai import OpenAI
from openai.types.responses import Response
from pydantic import BaseModel

from utilities.exceptions import DataTransformationError
from utilities.logger import get_logger
from utilities.types import JsonLLMResponse

T = TypeVar("T", bound=BaseModel)

GPT_MODEL = "gpt-4.1-mini"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)


log_handler = get_logger(__name__)


class OpenAILLMClient:
    """
    OpenAILLMClient: A client for interacting with
    OpenAI's LLMs to extract structured data.
    """
    def __init__(self):
        self.client = OPENAI_CLIENT

    def _call_llm(
        self,
        prompt: str,
        system_prompt: str,
        data_model: type[T],
    ) -> Response:
        """
        Call the LLM with the given
        prompt and system prompt, and
        return the raw response.
        """
        try:
            return self.client.responses.create(
                model=GPT_MODEL,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": data_model.__name__,
                        "schema": data_model.model_json_schema(),
                        "strict": True,
                    }
                },
            )
        except Exception as e:
            log_handler.error(f"Error calling LLM: {e}")
            raise

    def _extract_llm_json_response(
        self,
        response: Response
    ) -> JsonLLMResponse:
        """
        Extract JSON content from the LLM response, handling
        different response formats.
        """
        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "output_text":
                    return content.text
        raise DataTransformationError(
            "No text content found in LLM response"
        )

    def extract_structured(
        self,
        prompt: str,
        system_prompt: str,
        data_model: type[T],
        max_retries: int,
    ) -> T:
        """
        Extract structured data from the LLM response, with retries.
        """
        for _ in range(max_retries):
            response = self._call_llm(prompt, system_prompt, data_model)
            text = self._extract_llm_json_response(response)

            try:
                parsed = json.loads(text)
                return data_model(**parsed)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                log_handler.error(f"Error occurred while parsing JSON: {e}")
                continue
        raise DataTransformationError(
            "Failed to extract structured output"
        )
