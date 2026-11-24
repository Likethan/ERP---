# ruff: noqa: F403, F405
"""CampusOS Permission Registry and System Role Definitions.

All permissions follow the atomic format: {domain}:{resource}:{action}
"""

from app.core.permissions.catalog import ALL_PERMISSIONS
from app.core.permissions.constants import *  # noqa: F403
from app.core.permissions.constants import PermissionDefinition
from app.core.permissions.roles import DEFAULT_ROLE_PERMISSIONS

__all__ = [
    "ALL_PERMISSIONS",
    "DEFAULT_ROLE_PERMISSIONS",
    "PermissionDefinition",
]
