"""Tests for role-based access control."""

import pytest
from fastapi import HTTPException

from app.core.authorization import Permission, ROLE_PERMISSIONS, authorize
from app.core.security import AuthenticatedUser, UserRole


def user_with_role(role: UserRole) -> AuthenticatedUser:
    return AuthenticatedUser(user_id=f"{role.value}-user", role=role)


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (UserRole.VIEWER, Permission.VIEW_REPORT),
        (UserRole.ANALYST, Permission.VIEW_REPORT),
        (UserRole.ANALYST, Permission.GENERATE_REPORT),
        (UserRole.ADMIN, Permission.VIEW_REPORT),
        (UserRole.ADMIN, Permission.GENERATE_REPORT),
        (UserRole.ADMIN, Permission.ADMINISTER_SYSTEM),
    ],
)
def test_allows_explicitly_granted_permissions(
    role: UserRole,
    permission: Permission,
) -> None:
    user = user_with_role(role)

    assert authorize(user, permission) is user


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (UserRole.VIEWER, Permission.GENERATE_REPORT),
        (UserRole.VIEWER, Permission.ADMINISTER_SYSTEM),
        (UserRole.ANALYST, Permission.ADMINISTER_SYSTEM),
    ],
)
def test_denies_permissions_not_granted_to_role(
    role: UserRole,
    permission: Permission,
) -> None:
    with pytest.raises(HTTPException) as error:
        authorize(user_with_role(role), permission)

    assert error.value.status_code == 403
    assert error.value.detail == "Insufficient permissions"


def test_role_permission_sets_are_immutable() -> None:
    assert all(isinstance(permissions, frozenset) for permissions in ROLE_PERMISSIONS.values())
