"""Tests for centralized secure error responses."""

from fastapi.testclient import TestClient

from app.services.intent_service import intent_service
from tests.test_ask_api import ANALYST_KEY, app, ask


def test_error_body_and_header_share_request_id() -> None:
    response = ask("Generate a sales report", None)

    assert response.status_code == 401
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_validation_error_does_not_echo_sensitive_input() -> None:
    sensitive_value = "sensitive-value-that-must-not-be-returned"
    response = TestClient(app).post(
        "/ask",
        json={"question": sensitive_value, "unexpected": sensitive_value},
        headers={"X-API-Key": ANALYST_KEY},
    )

    assert response.status_code == 422
    assert sensitive_value not in response.text
    assert response.json()["error"]["code"] == "invalid_request"


def test_unhandled_exception_hides_internal_details(monkeypatch: object) -> None:
    sensitive_failure = "database password was accidentally exposed"

    def fail_safely(question: str) -> object:
        del question
        raise RuntimeError(sensitive_failure)

    getattr(monkeypatch, "setattr")(intent_service, "detect_intent", fail_safely)
    safe_client = TestClient(app, raise_server_exceptions=False)
    response = safe_client.post(
        "/ask",
        json={"question": "Generate a sales report"},
        headers={"X-API-Key": ANALYST_KEY},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["message"] == "An unexpected error occurred"
    assert sensitive_failure not in response.text
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
