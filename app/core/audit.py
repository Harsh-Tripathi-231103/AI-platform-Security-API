"""Structured, secret-safe security audit logging."""

from contextvars import ContextVar, Token
from datetime import UTC, datetime
from enum import StrEnum
import json
import logging


audit_logger = logging.getLogger("security.audit")
audit_logger.setLevel(logging.INFO)

_request_id: ContextVar[str] = ContextVar("request_id", default="unavailable")


class AuditEvent(StrEnum):
    """Security-relevant events emitted by the application."""

    AUTHENTICATION_SUCCEEDED = "authentication_succeeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_SUCCEEDED = "authorization_succeeded"
    AUTHORIZATION_FAILED = "authorization_failed"
    REQUEST_REJECTED = "request_rejected"
    BUSINESS_ACTION_SUCCEEDED = "business_action_succeeded"
    BUSINESS_ACTION_FAILED = "business_action_failed"
    INTERNAL_ERROR = "internal_error"


def configure_logging(log_level: str) -> None:
    """Configure application logging without placing secrets in the format."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(levelname)s %(name)s %(message)s",
    )


def set_request_id(request_id: str) -> Token[str]:
    """Bind a request ID to the current async execution context."""
    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous request context."""
    _request_id.reset(token)


def get_request_id() -> str:
    """Return the current server-generated request ID."""
    return _request_id.get()


def record_audit_event(
    event: AuditEvent,
    *,
    outcome: str,
    user_id: str | None = None,
    role: str | None = None,
    action: str | None = None,
    reason: str | None = None,
) -> None:
    """Write one constrained JSON event; arbitrary request data is not accepted."""
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": get_request_id(),
        "event": event.value,
        "outcome": outcome,
        "user_id": user_id,
        "role": role,
        "action": action,
        "reason": reason,
    }
    audit_logger.info(
        json.dumps(
            {key: value for key, value in payload.items() if value is not None},
            separators=(",", ":"),
            sort_keys=True,
        )
    )
