import json
from typing import Any

from openai import OpenAI
from pydantic import BaseModel


class OpenAIResponsesClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        payload: dict[str, Any],
        schema: type[BaseModel],
    ) -> dict[str, Any]:
        resp = self.client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                }
            },
        )
        text = getattr(resp, "output_text", "")
        if not text:
            raise ValueError("No output_text from model")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback when model/provider ignores structured output settings.
            return schema.model_validate_json(text).model_dump()


class MockLLMClient:
    def __init__(self, fixtures: dict[str, dict[str, Any]]):
        self.fixtures = fixtures

    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        payload: dict[str, Any],
        schema: type[BaseModel],
    ) -> dict[str, Any]:
        del model, payload, schema
        for key, value in self.fixtures.items():
            if key in system_prompt:
                return value
        raise KeyError("No fixture for prompt")
