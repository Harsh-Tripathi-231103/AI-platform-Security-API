"""Tests for structured, secret-safe audit events."""

import json
import logging

from app.core.audit import audit_logger
from tests.test_ask_api import ANALYST_KEY, client


def audit_payloads(caplog: object) -> list[dict[str, str]]:
    records = getattr(caplog, "records")
    return [json.loads(record.message) for record in records if record.name == audit_logger.name]


def test_successful_action_emits_traceable_audit_events(caplog: object) -> None:
    with getattr(caplog, "at_level")(logging.INFO, logger=audit_logger.name):
        response = client.post(
            "/ask",
            json={"question": "Generate this week's sales report."},
            headers={"X-API-Key": ANALYST_KEY},
        )

    payloads = audit_payloads(caplog)
    event_names = {payload["event"] for payload in payloads}
    assert response.status_code == 200
    assert {
        "authentication_succeeded",
        "authorization_succeeded",
        "business_action_succeeded",
    } <= event_names
    assert all(
        payload["request_id"] == response.headers["X-Request-ID"]
        for payload in payloads
    )


def test_failed_authentication_never_logs_key_or_question(caplog: object) -> None:
    invalid_key = "secret-value-that-must-not-be-logged"
    question = "confidential question that must not be logged"

    with getattr(caplog, "at_level")(logging.INFO, logger=audit_logger.name):
        response = client.post(
            "/ask",
            json={"question": question},
            headers={"X-API-Key": invalid_key},
        )

    rendered_logs = "\n".join(record.message for record in getattr(caplog, "records"))
    assert response.status_code == 401
    assert "authentication_failed" in rendered_logs
    assert invalid_key not in rendered_logs
    assert question not in rendered_logs
