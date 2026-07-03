"""Tests for strict API request validation."""

import pytest
from pydantic import ValidationError

from app.models.schemas import AskRequest


def test_accepts_and_normalizes_valid_question() -> None:
    request = AskRequest(question="  Generate this week's sales report.  ")
    assert request.question == "Generate this week's sales report."


@pytest.mark.parametrize("question", ["", "  ", "ab"])
def test_rejects_question_that_is_too_short(question: str) -> None:
    with pytest.raises(ValidationError):
        AskRequest(question=question)


def test_rejects_question_that_is_too_long() -> None:
    with pytest.raises(ValidationError):
        AskRequest(question="a" * 501)


def test_rejects_non_string_question() -> None:
    with pytest.raises(ValidationError):
        AskRequest(question=123)  # type: ignore[arg-type]


def test_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        AskRequest(question="Generate a report", api_key="do-not-put-secrets-here")


def test_rejects_control_characters() -> None:
    with pytest.raises(ValidationError):
        AskRequest(question="Generate\x00report")
