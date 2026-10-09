"""Pydantic v2 Schemas for Enterprise Administration & Policy Management (Step 23)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.configuration import (
    ConfigurationDataType,
    ConfigurationScope,
    ConfigurationSensitivity,
    ConfigurationStatus,
    DependencyCriticality,
    NumberingResetFrequency,
    PolicyScope,
    PolicyStatus,
)

# -----------------------------------------------------------------------------
# 1. Configuration Definitions
# -----------------------------------------------------------------------------


class ConfigurationDefinitionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(..., max_length=128, description="Unique configuration dot-notation key")
    name: str = Field(..., max_length=255, description="Human-readable configuration name")
    description: str | None = None
    category: str = Field(
        ..., max_length=64, description="Functional category (e.g. ATTENDANCE, FINANCE)"
    )
    module: str = Field(..., max_length=64, description="Module code")
    data_type: ConfigurationDataType = ConfigurationDataType.STRING
    default_value: Any | None = None
    validation_schema: dict[str, Any] | None = None
    allowed_values: list[Any] | None = None
    sensitivity: ConfigurationSensitivity = ConfigurationSensitivity.INTERNAL
    scope: ConfigurationScope = ConfigurationScope.TENANT
    is_editable: bool = True
    is_restart_required: bool = False
    is_feature_flag: bool = False
    is_active: bool = True


class ConfigurationDefinitionCreate(ConfigurationDefinitionBase):
    pass


class ConfigurationDefinitionUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=64)
    module: str | None = Field(None, max_length=64)
    data_type: ConfigurationDataType | None = None
    default_value: Any | None = None
    validation_schema: dict[str, Any] | None = None
    allowed_values: list[Any] | None = None
    sensitivity: ConfigurationSensitivity | None = None
    scope: ConfigurationScope | None = None
    is_editable: bool | None = None
    is_restart_required: bool | None = None
    is_feature_flag: bool | None = None
    is_active: bool | None = None


class ConfigurationDefinitionResponse(ConfigurationDefinitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 2. Configuration Values
# -----------------------------------------------------------------------------


class ConfigurationValueCreate(BaseModel):
    configuration_definition_id: UUID | None = None
    key: str | None = Field(None, description="Configuration key if definition ID is omitted")
    scope_type: ConfigurationScope = ConfigurationScope.TENANT
    campus_id: UUID | None = None
    institution_id: UUID | None = None
    value: Any = Field(..., description="Configuration payload")
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    reason: str | None = Field(None, description="Rationale for the update")


class ConfigurationValueUpdate(BaseModel):
    value: Any = Field(..., description="Updated configuration payload")
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    reason: str | None = Field(None, description="Rationale for the update")
    status: ConfigurationStatus | None = None


class ConfigurationValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    configuration_definition_id: UUID
    key: str | None = None
    tenant_id: UUID | None = None
    institution_id: UUID | None = None
    campus_id: UUID | None = None
    scope_type: ConfigurationScope
    value: Any
    source: str
    version: int
    status: ConfigurationStatus
    effective_from: datetime
    effective_until: datetime | None = None
    created_by_id: UUID | None = None
    updated_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 3. Effective Configuration Resolution
# -----------------------------------------------------------------------------


class ConfigurationEffectiveResponse(BaseModel):
    key: str
    value: Any
    data_type: ConfigurationDataType
    source_scope: str
    source_id: UUID | None = None
    configuration_version: int | None = None
    is_override: bool
    effective_from: datetime | None = None
    sensitivity: ConfigurationSensitivity


class ConfigurationEffectiveListResponse(BaseModel):
    tenant_id: UUID
    campus_id: UUID | None = None
    items: list[ConfigurationEffectiveResponse]


# -----------------------------------------------------------------------------
# 4. Validation & Preview
# -----------------------------------------------------------------------------


class ConfigurationValidateRequest(BaseModel):
    key: str
    value: Any


class ConfigurationValidateResponse(BaseModel):
    valid: bool
    key: str
    data_type: ConfigurationDataType
    errors: list[str] = []


class ConfigurationPreviewRequest(BaseModel):
    key: str
    proposed_value: Any
    scope_type: ConfigurationScope = ConfigurationScope.TENANT
    campus_id: UUID | None = None


class ImpactedConsumer(BaseModel):
    consumer_module: str
    consumer_component: str
    impact_description: str
    criticality: DependencyCriticality
    is_restart_required: bool


class ConfigurationPreviewResponse(BaseModel):
    key: str
    current_value: Any | None = None
    proposed_value: Any
    validation_status: bool
    validation_errors: list[str] = []
    current_source: str
    target_scope: ConfigurationScope
    impacted_consumers: list[ImpactedConsumer] = []
    restart_required: bool = False


# -----------------------------------------------------------------------------
# 5. Versioning & Rollback
# -----------------------------------------------------------------------------


class ConfigurationVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    configuration_definition_id: UUID
    configuration_value_id: UUID | None = None
    version_number: int
    previous_version: int | None = None
    value: Any
    change_summary: str | None = None
    changed_fields: list[str] | None = None
    actor_id: UUID | None = None
    actor_email: str | None = None
    reason: str | None = None
    status: ConfigurationStatus
    effective_from: datetime
    rollback_reference: UUID | None = None
    created_at: datetime


class ConfigurationRollbackRequest(BaseModel):
    target_version_number: int | None = None
    target_version_id: UUID | None = None
    reason: str = Field(..., min_length=3, description="Justification for rollback")


# -----------------------------------------------------------------------------
# 6. Business Policy Engine
# -----------------------------------------------------------------------------


class PolicyRuleCondition(BaseModel):
    field: str = Field(..., description="Context attribute name to evaluate")
    operator: str = Field(
        ...,
        description="Operator (eq, neq, gt, gte, lt, lte, in, not_in, contains, between)",
    )
    value: Any = Field(..., description="Expected value or boundary")


class PolicyCreate(BaseModel):
    policy_key: str = Field(..., max_length=128)
    name: str = Field(..., max_length=255)
    description: str | None = None
    module: str = Field(..., max_length=64)
    scope: PolicyScope = PolicyScope.TENANT
    campus_id: UUID | None = None
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    actions: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    status: PolicyStatus = PolicyStatus.ACTIVE
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class PolicyUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    conditions: list[dict[str, Any]] | None = None
    actions: dict[str, Any] | None = None
    priority: int | None = None
    status: PolicyStatus | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    reason: str | None = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    policy_key: str
    name: str
    description: str | None = None
    module: str
    scope: PolicyScope
    campus_id: UUID | None = None
    conditions: list[dict[str, Any]]
    actions: dict[str, Any]
    priority: int
    status: PolicyStatus
    version: int
    effective_from: datetime
    effective_until: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PolicyEvaluateRequest(BaseModel):
    context: dict[str, Any] = Field(
        ..., description="Operational payload attributes to evaluate against conditions"
    )
    campus_id: UUID | None = None


class PolicyEvaluateResponse(BaseModel):
    policy: str
    decision: bool
    actions: dict[str, Any]
    matched_conditions: int
    total_conditions: int
    version: int
    evaluation_context: dict[str, Any]


# -----------------------------------------------------------------------------
# 7. Feature Flags
# -----------------------------------------------------------------------------


class FeatureFlagCreate(BaseModel):
    key: str = Field(..., max_length=128)
    name: str = Field(..., max_length=255)
    description: str | None = None
    module: str = Field(..., max_length=64)
    is_enabled: bool = False
    rollout_percentage: int = Field(0, ge=0, le=100)
    target_roles: list[str] | None = None
    target_users: list[str] | None = None
    environment: str = "ALL"
    effective_from: datetime | None = None
    expires_at: datetime | None = None


class FeatureFlagUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None
    rollout_percentage: int | None = Field(None, ge=0, le=100)
    target_roles: list[str] | None = None
    target_users: list[str] | None = None
    environment: str | None = None
    effective_from: datetime | None = None
    expires_at: datetime | None = None


class FeatureFlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    key: str
    name: str
    description: str | None = None
    module: str
    is_enabled: bool
    rollout_percentage: int
    target_roles: list[str] | None = None
    target_users: list[str] | None = None
    environment: str
    effective_from: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class FeatureFlagEvaluateRequest(BaseModel):
    user_id: UUID | None = None
    roles: list[str] | None = None
    environment: str | None = None


class FeatureFlagEvaluateResponse(BaseModel):
    key: str
    is_enabled: bool
    reason: str


# -----------------------------------------------------------------------------
# 8. Module Configurations
# -----------------------------------------------------------------------------


class ModuleConfigurationUpdate(BaseModel):
    is_enabled: bool | None = None
    enabled_features: list[str] | None = None
    maintenance_mode: bool | None = None
    maintenance_message: str | None = None
    custom_settings: dict[str, Any] | None = None


class ModuleConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    module: str
    is_enabled: bool
    enabled_features: list[str] | None = None
    maintenance_mode: bool
    maintenance_message: str | None = None
    custom_settings: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 9. Numbering Sequences
# -----------------------------------------------------------------------------


class NumberingSequenceCreate(BaseModel):
    sequence_key: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: str | None = None
    prefix: str = Field("", max_length=32)
    suffix: str | None = Field(None, max_length=32)
    pattern: str = Field("{PREFIX}{YYYY}-{SEQ}", max_length=128)
    padding: int = Field(5, ge=1, le=12)
    current_val: int = Field(0, ge=0)
    step: int = Field(1, ge=1, le=100)
    reset_frequency: NumberingResetFrequency = NumberingResetFrequency.NEVER


class NumberingSequenceUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    prefix: str | None = Field(None, max_length=32)
    suffix: str | None = Field(None, max_length=32)
    pattern: str | None = Field(None, max_length=128)
    padding: int | None = Field(None, ge=1, le=12)
    step: int | None = Field(None, ge=1, le=100)
    reset_frequency: NumberingResetFrequency | None = None
    is_active: bool | None = None


class NumberingSequenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    sequence_key: str
    name: str
    description: str | None = None
    prefix: str
    suffix: str | None = None
    pattern: str
    padding: int
    current_val: int
    step: int
    reset_frequency: NumberingResetFrequency
    last_reset_year: int | None = None
    last_reset_month: int | None = None
    last_reset_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SequenceGenerateResponse(BaseModel):
    sequence_key: str
    generated_number: str
    current_val: int


# -----------------------------------------------------------------------------
# 10. Configuration Dependencies
# -----------------------------------------------------------------------------


class ConfigurationDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    configuration_key: str
    consumer_module: str
    consumer_component: str
    impact_description: str
    criticality: DependencyCriticality
    is_restart_required: bool
    created_at: datetime
    updated_at: datetime
