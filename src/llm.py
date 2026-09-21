"""JSON extraction and Pydantic validation for LLM responses."""
from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import TypeAdapter, ValidationError

T = TypeVar("T")

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class JsonParseError(ValueError):
    """Raised when a model response does not contain valid JSON for the schema."""


def extract_json(text: str) -> Any:
    """Pull the first JSON object or array out of a model response."""
    if not text or not text.strip():
        raise JsonParseError("Empty model response.")

    stripped = _FENCE_RE.sub("", text.strip()).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char not in "{[":
            continue
        try:
            obj, _ = decoder.raw_decode(stripped[index:])
            return obj
        except json.JSONDecodeError:
            continue
    raise JsonParseError("No JSON object or array found in model response.")


def parse_as(text: str, model: type[T]) -> T:
    """Extract JSON and validate it against a Pydantic model or type."""
    payload = extract_json(text)
    try:
        return TypeAdapter(model).validate_python(payload)
    except ValidationError as exc:
        raise JsonParseError(f"Response did not match {model}: {exc}") from exc


def response_text(response: Any) -> str:
    """Flatten Anthropic message content blocks into a single string."""
    chunks: list[str] = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            chunks.append(text)
    if chunks:
        return "\n".join(chunks)
    return str(response)


def complete_json(
    client: Any,
    *,
    system: str,
    user: str,
    model: type[T],
    model_name: str,
    max_tokens: int,
    retry: bool = True,
) -> T:
    """Call the Anthropic Messages API and parse a schema-valid JSON payload.

    Retries once with a stricter instruction if the first response fails validation.
    """
    response = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = response_text(response)
    try:
        return parse_as(text, model)
    except JsonParseError:
        if not retry:
            raise
        follow_up = (
            f"{user}\n\nYour previous reply was not valid JSON for the required schema. "
            "Return ONLY valid JSON. Do not wrap it in markdown. Do not invent numbers "
            "you cannot cite."
        )
        return complete_json(
            client,
            system=system,
            user=follow_up,
            model=model,
            model_name=model_name,
            max_tokens=max_tokens,
            retry=False,
        )
