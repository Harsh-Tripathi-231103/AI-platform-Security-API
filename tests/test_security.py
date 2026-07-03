"""Tests for API-key authentication."""

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import UserRole, authenticate_api_key


VIEWER_KEY = "viewer-key-1234567890"
ANALYST_KEY = "analyst-key-12345678"
ADMIN_KEY = "admin-key-1234567890"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        viewer_api_key=VIEWER_KEY,
        analyst_api_key=ANALYST_KEY,
        admin_api_key=ADMIN_KEY,
    )


@pytest.mark.parametrize(
    ("api_key", "expected_user", "expected_role"),
    [
        (VIEWER_KEY, "viewer-user", UserRole.VIEWER),
        (ANALYST_KEY, "analyst-user", UserRole.ANALYST),
        (ADMIN_KEY, "admin-user", UserRole.ADMIN),
    ],
)
def test_authenticates_each_configured_role(
    settings: Settings,
    api_key: str,
    expected_user: str,
    expected_role: UserRole,
) -> None:
    user = authenticate_api_key(api_key=api_key, settings=settings)

    assert user.user_id == expected_user
    assert user.role is expected_role


@pytest.mark.parametrize("api_key", [None, "", "wrong-key-123456789"])
def test_rejects_missing_or_invalid_api_key(
    settings: Settings,
    api_key: str | None,
) -> None:
    with pytest.raises(HTTPException) as error:
        authenticate_api_key(api_key=api_key, settings=settings)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid or missing API key"
    assert error.value.headers == {"WWW-Authenticate": "ApiKey"}


def test_rejects_duplicate_role_keys() -> None:
    with pytest.raises(ValidationError, match="API keys must be unique"):
        Settings(
            viewer_api_key=VIEWER_KEY,
            analyst_api_key=VIEWER_KEY,
            admin_api_key=ADMIN_KEY,
        )
