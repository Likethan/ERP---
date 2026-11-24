"""SQLAlchemy Entities for Enterprise Administration, Configuration & Policy Management (Step 23).

Centralized control plane for configurable CampusOS behavior:
- Configuration Definitions, Values, Versions & Rollback
- Business Policy Engine & Policy Versions
- Tenant Feature Flags
- Module Enablement & Maintenance Mode
- Numbering & Concurrency-Safe Sequence Management
- Configuration Dependency Registry for Impact Analysis
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class ConfigurationDataType(StrEnum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"
    DATE = "DATE"
    DATETIME = "DATETIME"
    DURATION = "DURATION"
    PERCENTAGE = "PERCENTAGE"
    CURRENCY = "CURRENCY"
    URL = "URL"
    JSON = "JSON"


class ConfigurationSensitivity(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class ConfigurationScope(StrEnum):
    PLATFORM = "PLATFORM"
    TENANT = "TENANT"
    INSTITUTION = "INSTITUTION"
    CAMPUS = "CAMPUS"
    MODULE = "MODULE"


class ConfigurationStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"
    EXPIRED = "EXPIRED"


class PolicyScope(StrEnum):
    PLATFORM = "PLATFORM"
    TENANT = "TENANT"
    CAMPUS = "CAMPUS"


class PolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class NumberingResetFrequency(StrEnum):
    NEVER = "NEVER"
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"


class DependencyCriticality(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# -----------------------------------------------------------------------------
# 2. Configuration Definitions
# -----------------------------------------------------------------------------


class ConfigurationDefinition(BaseModel):
    """Supported configurable parameter specification and schema."""

    __tablename__ = "configuration_definitions"
    __table_args__ = (
        Index("idx_cfg_def_category", "category"),
        Index("idx_cfg_def_module", "module"),
        Index("idx_cfg_def_active", "is_active"),
    )

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    data_type: Mapped[str] = mapped_column(
        String(32), default=ConfigurationDataType.STRING, nullable=False
    )
    default_value: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    validation_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    allowed_values: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    sensitivity: Mapped[str] = mapped_column(
        String(32), default=ConfigurationSensitivity.INTERNAL, nullable=False
    )
    scope: Mapped[str] = mapped_column(
        String(32), default=ConfigurationScope.TENANT, nullable=False
    )
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_restart_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_feature_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    values: Mapped[list["ConfigurationValue"]] = relationship(
        back_populates="definition", cascade="all, delete-orphan"
    )
    versions: Mapped[list["ConfigurationVersion"]] = relationship(
        back_populates="definition", cascade="all, delete-orphan"
    )


# -----------------------------------------------------------------------------
# 3. Configuration Values
# -----------------------------------------------------------------------------


class ConfigurationValue(BaseModel):
    """Configured parameter value override scoped to tenant, institution, or campus."""

    __tablename__ = "configuration_values"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "configuration_definition_id",
            "scope_type",
            "campus_id",
            name="uq_cfg_val_scoped",
        ),
        Index("idx_cfg_val_tenant_def", "tenant_id", "configuration_definition_id"),
        Index("idx_cfg_val_status", "status"),
        Index("idx_cfg_val_scope_type", "scope_type"),
    )

    configuration_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("configuration_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    institution_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(
        String(32), default=ConfigurationScope.TENANT, nullable=False
    )
    value: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="TENANT_OVERRIDE", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ConfigurationStatus.ACTIVE, nullable=False
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    definition: Mapped["ConfigurationDefinition"] = relationship(back_populates="values")


# -----------------------------------------------------------------------------
# 4. Configuration Versions & Audit History
# -----------------------------------------------------------------------------


class ConfigurationVersion(BaseModel):
    """Immutable audit trail for every configuration change and rollback."""

    __tablename__ = "configuration_versions"
    __table_args__ = (
        Index("idx_cfg_ver_tenant_def", "tenant_id", "configuration_definition_id"),
        Index("idx_cfg_ver_num", "configuration_definition_id", "version_number"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    configuration_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("configuration_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    configuration_value_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("configuration_values.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ConfigurationStatus.ACTIVE, nullable=False
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    rollback_reference: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    # Relationships
    definition: Mapped["ConfigurationDefinition"] = relationship(back_populates="versions")


# -----------------------------------------------------------------------------
# 5. Business Policies & Policy Versions
# -----------------------------------------------------------------------------


class ConfigurationPolicy(BaseModel):
    """Reusable business policy containing declarative conditions and actions."""

    __tablename__ = "configuration_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_key", "campus_id", name="uq_cfg_policy_scoped"),
        Index("idx_cfg_policy_tenant_key", "tenant_id", "policy_key"),
        Index("idx_cfg_policy_module", "module"),
        Index("idx_cfg_policy_status", "status"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    policy_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default=PolicyScope.TENANT, nullable=False)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    actions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PolicyStatus.ACTIVE, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list["ConfigurationPolicyVersion"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class ConfigurationPolicyVersion(BaseModel):
    """Historical version snapshot for business policies."""

    __tablename__ = "configuration_policy_versions"
    __table_args__ = (Index("idx_cfg_pol_ver_policy_num", "policy_id", "version_number"),)

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    policy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("configuration_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    actions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    policy: Mapped["ConfigurationPolicy"] = relationship(back_populates="versions")


# -----------------------------------------------------------------------------
# 6. Feature Flags
# -----------------------------------------------------------------------------


class FeatureFlag(BaseModel):
    """Controlled feature flag with environment awareness, targeting, and rollout percentages."""

    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_feature_flag_tenant_key"),
        Index("idx_feat_flag_tenant_key", "tenant_id", "key"),
        Index("idx_feat_flag_module", "module"),
        Index("idx_feat_flag_enabled", "is_enabled"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_roles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    target_users: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    environment: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


# -----------------------------------------------------------------------------
# 7. Module Configurations
# -----------------------------------------------------------------------------


class ModuleConfiguration(BaseModel):
    """Module enablement, feature toggles, and maintenance state per tenant."""

    __tablename__ = "module_configurations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "module", name="uq_module_config_tenant_module"),
        Index("idx_mod_cfg_tenant_module", "tenant_id", "module"),
        Index("idx_mod_cfg_enabled", "is_enabled"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled_features: Mapped[list[str] | None] = mapped_column(JSONB, default=list, nullable=True)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintenance_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, default=dict, nullable=True
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


# -----------------------------------------------------------------------------
# 8. Numbering Sequences
# -----------------------------------------------------------------------------


class NumberingSequence(BaseModel):
    """Concurrency-safe sequence counter and identifier generator."""

    __tablename__ = "numbering_sequences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sequence_key", name="uq_numbering_seq_tenant_key"),
        Index("idx_num_seq_tenant_key", "tenant_id", "sequence_key"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prefix: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    suffix: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pattern: Mapped[str] = mapped_column(
        String(128), default="{PREFIX}{YYYY}-{SEQ}", nullable=False
    )
    padding: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_val: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reset_frequency: Mapped[str] = mapped_column(
        String(32), default=NumberingResetFrequency.NEVER, nullable=False
    )
    last_reset_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_reset_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# -----------------------------------------------------------------------------
# 9. Configuration Dependencies (Impact Analysis Registry)
# -----------------------------------------------------------------------------


class ConfigurationDependency(BaseModel):
    """Registry of system components consuming configuration keys for impact analysis."""

    __tablename__ = "configuration_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "configuration_key",
            "consumer_module",
            "consumer_component",
            name="uq_cfg_dep_key_consumer",
        ),
        Index("idx_cfg_dep_key", "configuration_key"),
        Index("idx_cfg_dep_module", "consumer_module"),
    )

    configuration_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    consumer_module: Mapped[str] = mapped_column(String(64), nullable=False)
    consumer_component: Mapped[str] = mapped_column(String(128), nullable=False)
    impact_description: Mapped[str] = mapped_column(Text, nullable=False)
    criticality: Mapped[str] = mapped_column(
        String(32), default=DependencyCriticality.MEDIUM, nullable=False
    )
    is_restart_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
