"""Read-Only Institutional Configuration & Policy Tools for Intelligence Layer (Step 23)."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import CONFIGURATION_READ
from app.domains.intelligence.tools.base import ToolDefinition, ToolParameter
from app.models.configuration import ConfigurationSensitivity
from app.models.people import User
from app.services.configuration_resolver import ConfigurationResolver
from app.services.module_configuration_service import ModuleConfigurationService


async def handle_get_effective_configuration(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler fetching effective configuration parameter for tenant."""
    key = params.get("key")
    if not key:
        return {"error": "Configuration key is required"}

    try:
        eff = await ConfigurationResolver.get_effective_config(
            db=db,
            tenant_id=tenant_id,
            key=key,
            use_cache=True,
        )
    except Exception as exc:
        return {"error": str(exc)}

    # Governance check: forbid AI exposure of RESTRICTED / CONFIDENTIAL configuration
    if eff.sensitivity in (
        ConfigurationSensitivity.RESTRICTED,
        ConfigurationSensitivity.CONFIDENTIAL,
    ):
        return {
            "key": key,
            "error": "This configuration setting has a RESTRICTED or CONFIDENTIAL sensitivity level and cannot be exposed to AI summaries.",
        }

    return {
        "key": eff.key,
        "value": eff.value,
        "data_type": eff.data_type,
        "source_scope": eff.source_scope,
        "is_override": eff.is_override,
    }


async def handle_get_module_status(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler fetching module enablement and maintenance states."""
    modules = await ModuleConfigurationService.list_module_configs(db=db, tenant_id=tenant_id)
    return {
        "modules": [
            {
                "module": m.module,
                "is_enabled": m.is_enabled,
                "maintenance_mode": m.maintenance_mode,
            }
            for m in modules
        ]
    }


CONFIGURATION_TOOLS = [
    ToolDefinition(
        name="get_effective_configuration",
        domain="CONFIGURATION",
        description="Lookup the effective institution-wide or tenant configuration setting for a parameter key (e.g. attendance threshold, currency, invoice due days).",
        required_permissions=[CONFIGURATION_READ],
        parameters=[
            ToolParameter(
                name="key",
                type="string",
                required=True,
                description="Configuration key in dot-notation (e.g., attendance.minimum_percentage, finance.currency)",
            )
        ],
        handler=handle_get_effective_configuration,
        sensitivity_level="INTERNAL",
    ),
    ToolDefinition(
        name="get_module_enablement_status",
        domain="CONFIGURATION",
        description="Check which CampusOS ERP modules are currently enabled or under maintenance for the institution.",
        required_permissions=[CONFIGURATION_READ],
        parameters=[],
        handler=handle_get_module_status,
        sensitivity_level="INTERNAL",
    ),
]
