"""LLM call via LiteLLM -> OpenRouter -> Cerebras, per the `cerebras` skill."""

from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

from llm.schema import ChatCompletion

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


def call_llm(messages: list[dict]) -> ChatCompletion:
    """Request a structured-output completion and parse it into `ChatCompletion`."""
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatCompletion,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    content = response.choices[0].message.content
    return ChatCompletion.model_validate_json(content)
