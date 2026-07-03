"""Role-based access control for protected business actions."""

from collections.abc import Callable
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.audit import AuditEvent, record_audit_event
from app.core.security import AuthenticatedUser, UserRole, authenticate_api_key


class Permission(StrEnum):
    """Fine-grained permissions enforced by the application."""

    VIEW_REPORT = "view_report"
    GENERATE_REPORT = "generate_report"
    ADMINISTER_SYSTEM = "administer_system"


# Permissions are granted explicitly. Anything absent is denied by default.
ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.VIEWER: frozenset({Permission.VIEW_REPORT}),
    UserRole.ANALYST: frozenset(
        {
            Permission.VIEW_REPORT,
            Permission.GENERATE_REPORT,
        }
    ),
    UserRole.ADMIN: frozenset(Permission),
}


def authorize(
    user: AuthenticatedUser,
    permission: Permission,
) -> AuthenticatedUser:
    """Return the user when authorized, otherwise fail with a safe 403."""
    granted_permissions = ROLE_PERMISSIONS.get(user.role, frozenset())
    if permission not in granted_permissions:
        record_audit_event(
            AuditEvent.AUTHORIZATION_FAILED,
            outcome="failure",
            user_id=user.user_id,
            role=user.role.value,
            action=permission.value,
            reason="permission_denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    record_audit_event(
        AuditEvent.AUTHORIZATION_SUCCEEDED,
        outcome="success",
        user_id=user.user_id,
        role=user.role.value,
        action=permission.value,
    )
    return user


def require_permission(
    permission: Permission,
) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Build a FastAPI dependency that authenticates and authorizes a caller."""

    def permission_dependency(
        user: Annotated[AuthenticatedUser, Depends(authenticate_api_key)],
    ) -> AuthenticatedUser:
        return authorize(user, permission)

    return permission_dependency
