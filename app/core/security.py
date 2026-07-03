"""API-key authentication and authenticated caller identity."""

from enum import StrEnum
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings, get_settings


API_KEY_HEADER_NAME = "X-API-Key"

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER_NAME,
    scheme_name="Enterprise API key",
    description="API key assigned to an enterprise user role.",
    auto_error=False,
)


class UserRole(StrEnum):
    """Roles available to authenticated callers."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class AuthenticatedUser(BaseModel):
    """Trusted identity produced after successful authentication."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    role: UserRole


def _authentication_error() -> HTTPException:
    """Return the same safe response for missing and invalid credentials."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def authenticate_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    """Authenticate an API key and map it to a stable identity and role."""
    if not api_key:
        raise _authentication_error()

    credentials = (
        (settings.viewer_api_key.get_secret_value(), "viewer-user", UserRole.VIEWER),
        (settings.analyst_api_key.get_secret_value(), "analyst-user", UserRole.ANALYST),
        (settings.admin_api_key.get_secret_value(), "admin-user", UserRole.ADMIN),
    )

    for expected_key, user_id, role in credentials:
        if secrets.compare_digest(api_key, expected_key):
            return AuthenticatedUser(user_id=user_id, role=role)

    raise _authentication_error()
