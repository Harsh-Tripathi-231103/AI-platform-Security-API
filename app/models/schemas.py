"""Validated request and response contracts for the API."""

import unicodedata
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    """A strictly validated natural-language request."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(
        strict=True,
        min_length=3,
        max_length=500,
        description="The business question or action requested by the caller.",
        examples=["Generate this week's sales report."],
    )

    @field_validator("question")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        """Reject hidden control characters that can obscure malicious input."""
        if any(unicodedata.category(character) == "Cc" for character in value):
            raise ValueError("question must not contain control characters")
        return value


class ActionResult(BaseModel):
    """Structured details about a completed business action."""

    model_config = ConfigDict(extra="forbid")

    name: str
    data: dict[str, Any] = Field(default_factory=dict)


class AskResponse(BaseModel):
    """Successful response returned by the ask workflow."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    answer: str
    action: ActionResult | None = None


class ErrorDetail(BaseModel):
    """Safe, consistent error information returned to API clients."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """Top-level envelope for every controlled API error."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
