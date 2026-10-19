"""Pydantic v2 Schemas for Enterprise Reliability Engineering, Disaster Recovery & Business Continuity (Step 31)."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceCriticalityTier(StrEnum):
    TIER_1_CRITICAL = "TIER_1_CRITICAL"
    TIER_2_ESSENTIAL = "TIER_2_ESSENTIAL"
    TIER_3_DEGRADABLE = "TIER_3_DEGRADABLE"


class ServiceReliabilityTierInfo(BaseModel):
    service_name: str
    criticality_tier: ServiceCriticalityTier
    rto_minutes: int
    rpo_minutes: int
    degraded_behavior: str
    must_remain_operational: bool


class ReliabilityObjectivesResponse(BaseModel):
    availability_sla_percent: float = Field(..., description="Target SLA (excluding planned maintenance)")
    rto_tier_1_minutes: int = Field(..., description="Recovery Time Objective for Tier 1 Critical services")
    rto_tier_2_minutes: int = Field(..., description="Recovery Time Objective for Tier 2 Essential services")
    rto_tier_3_minutes: int = Field(..., description="Recovery Time Objective for Tier 3 Degradable services")
    rpo_database_minutes: int = Field(..., description="Recovery Point Objective for PostgreSQL database")
    rpo_documents_hours: int = Field(..., description="Recovery Point Objective for document object storage")
    backup_frequency: str = Field(..., description="Operational backup schedule")
    backup_retention_days: int = Field(..., description="Configured active retention window")
    restore_verification_frequency: str = Field(..., description="Scheduled sandbox restore frequency")
    max_outbox_queue_delay_seconds: int = Field(..., description="Max acceptable outbox processing delay")
    max_notification_queue_delay_seconds: int = Field(..., description="Max acceptable notification dispatch delay")
    services: list[ServiceReliabilityTierInfo]


class BackupCreateRequest(BaseModel):
    backup_type: str = Field(default="FULL", description="FULL, LOGICAL, or DIAGNOSTIC")
    retention_days: int = Field(default=30, ge=1, le=365)


class BackupRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    backup_type: str
    filename: str
    file_path: str
    size_bytes: int
    sha256_checksum: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float
    error_message: str | None = None
    retention_days: int
    is_known_good: bool
    verified_at: datetime | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class BackupPruneResponse(BaseModel):
    pruned_count: int
    retained_count: int
    protected_known_good_id: UUID | None = None
    message: str


class RestoreVerificationRequest(BaseModel):
    backup_record_id: UUID
    sandbox_database_name: str = Field(
        default="campusos_restore_sandbox",
        description="Isolated disposable sandbox database name",
    )


class RestoreVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    backup_record_id: UUID
    sandbox_database_name: str
    status: str
    sha256_verified: bool
    schema_verified: bool
    tables_verified_count: int
    table_row_counts_json: dict[str, Any] = Field(default_factory=dict)
    isolation_check_passed: bool
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float
    error_message: str | None = None


class CircuitBreakerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dependency_name: str
    state: str
    failure_count: int
    success_count: int
    consecutive_failures: int
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    last_state_change_at: datetime
    failure_threshold: int
    recovery_timeout_seconds: int


class CircuitBreakerResetRequest(BaseModel):
    reason: str = Field(default="Manual operator reset", min_length=3, max_length=255)


class StorageAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    total_db_records: int
    total_storage_files: int
    missing_files_count: int
    orphaned_files_count: int
    missing_file_keys: list[str] = Field(default_factory=list)
    orphaned_file_keys: list[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float
    error_message: str | None = None


class OutboxBacklogRecoveryResponse(BaseModel):
    recovered_count: int
    stuck_threshold_seconds: int
    dead_lettered_count: int = 0
    message: str


class PlatformReliabilityStatusResponse(BaseModel):
    overall_status: str = Field(..., description="HEALTHY, DEGRADED, or UNHEALTHY")
    last_backup_at: datetime | None = None
    last_successful_backup_at: datetime | None = None
    last_restore_verification_at: datetime | None = None
    last_restore_verification_status: str | None = None
    backup_freshness_status: str = Field(..., description="FRESH, WARNING, CRITICAL, or NO_BACKUPS")
    backup_age_hours: float | None = None
    outbox_pending_count: int
    outbox_processing_count: int
    outbox_dead_letter_count: int
    outbox_oldest_event_age_seconds: float
    outbox_queue_healthy: bool
    open_circuit_breakers_count: int
    circuit_breakers: list[CircuitBreakerResponse] = Field(default_factory=list)
    degraded_services: list[str] = Field(default_factory=list)
