"""Deterministic, zero-cost intent detection for allowlisted business actions."""

from enum import StrEnum
import re
from typing import Protocol
import unicodedata

from pydantic import BaseModel, ConfigDict, Field


class BusinessIntent(StrEnum):
    """Business actions the application knows how to handle safely."""

    GENERATE_SALES_REPORT = "generate_sales_report"
    UNKNOWN = "unknown"


class IntentDecision(BaseModel):
    """Structured output from intent detection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intent: BusinessIntent
    confidence: float = Field(ge=0, le=1)


class IntentService(Protocol):
    """Interface that a future local or hosted model can implement."""

    def detect_intent(self, question: str) -> IntentDecision:
        """Classify a validated question into an allowlisted intent."""
        ...


class RuleBasedIntentService:
    """Classify requests without an external model, network, or usage fees."""

    _action_terms = frozenset({"build", "create", "generate", "prepare", "produce"})
    _sales_terms = frozenset({"revenue", "sale", "sales"})
    _report_terms = frozenset({"report", "summary"})

    @staticmethod
    def _tokenize(question: str) -> frozenset[str]:
        normalized = unicodedata.normalize("NFKC", question).casefold()
        return frozenset(re.findall(r"[a-z]+", normalized))

    def detect_intent(self, question: str) -> IntentDecision:
        """Match only complete, explicitly supported business-action patterns."""
        tokens = self._tokenize(question)
        is_generate_report = (
            bool(tokens & self._action_terms)
            and bool(tokens & self._sales_terms)
            and bool(tokens & self._report_terms)
        )
        if is_generate_report:
            return IntentDecision(
                intent=BusinessIntent.GENERATE_SALES_REPORT,
                confidence=1.0,
            )

        return IntentDecision(intent=BusinessIntent.UNKNOWN, confidence=0.0)


intent_service: IntentService = RuleBasedIntentService()
