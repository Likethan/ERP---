"""Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement Models (Step 43).

Provides multi-tenant relational persistence for:
- Configurable Accreditation Frameworks (NAAC, NBA, ISO, Internal IQAC benchmarks) and Version Snapshots
- Criteria and Subcriteria Hierarchies with Weighting and Assessment Guidelines
- Assessment Cycles & Criterion-level Assessments with Scoring and Independent Review
- Evidence Repository with Traceability to Documents, Knowledge Items, and Records
- Quality Indicators (KPIs), Time-series Observations & Data Quality Validations
- Internal Quality Audit Programs, Checklists & Immutable Finalized Audit Reports
- Quality Findings, Corrective & Preventive Actions (CAPA) with Separation of Duties
- Continuous Quality Improvement (CQI) Plans & Outcome Evaluations
- Accreditation Readiness Snapshots and Gap Analysis
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSONB compatibility
JSONB_COMPAT = JSONB


# =============================================================================
# ENUMS & DOMAIN CONSTANTS
# =============================================================================


class AccreditationFrameworkType(StrEnum):
    NAAC = "NAAC"
    NBA = "NBA"
    NIRF = "NIRF"
    ISO_21001 = "ISO_21001"
    ABET = "ABET"
    INTERNAL_IQAC = "INTERNAL_IQAC"
    CUSTOM = "CUSTOM"


class AccreditationFrameworkStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class AccreditationScoringModel(StrEnum):
    NUMERIC_SCALE = "NUMERIC_SCALE"
    MATURITY_LEVEL = "MATURITY_LEVEL"
    PASS_FAIL = "PASS_FAIL"
    HYBRID = "HYBRID"


class AccreditationCriterionType(StrEnum):
    QUALITATIVE = "QUALITATIVE"
    QUANTITATIVE = "QUANTITATIVE"
    COMPLIANCE = "COMPLIANCE"


class AccreditationAssessmentStatus(StrEnum):
    UNASSESSED = "UNASSESSED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AccreditationMaturityLevel(StrEnum):
    LEVEL_1_INITIAL = "LEVEL_1_INITIAL"
    LEVEL_2_DEVELOPING = "LEVEL_2_DEVELOPING"
    LEVEL_3_DEFINED = "LEVEL_3_DEFINED"
    LEVEL_4_MANAGED = "LEVEL_4_MANAGED"
    LEVEL_5_OPTIMIZING = "LEVEL_5_OPTIMIZING"


class AccreditationEvidenceCategory(StrEnum):
    POLICY_SOP = "POLICY_SOP"
    EXAM_RECORD = "EXAM_RECORD"
    FACULTY_CREDENTIAL = "FACULTY_CREDENTIAL"
    STUDENT_DATA = "STUDENT_DATA"
    INFRASTRUCTURE_AUDIT = "INFRASTRUCTURE_AUDIT"
    GOVERNANCE_MINUTES = "GOVERNANCE_MINUTES"
    FINANCIAL_AUDIT = "FINANCIAL_AUDIT"
    SURVEY_FEEDBACK = "SURVEY_FEEDBACK"
    EXTERNAL_CERTIFICATE = "EXTERNAL_CERTIFICATE"


class AccreditationEvidenceVerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class QualityIndicatorCategory(StrEnum):
    ACADEMIC_EXCELLENCE = "ACADEMIC_EXCELLENCE"
    RESEARCH_INNOVATION = "RESEARCH_INNOVATION"
    STUDENT_SUCCESS = "STUDENT_SUCCESS"
    FACULTY_PROFILE = "FACULTY_PROFILE"
    INFRASTRUCTURE_RESOURCES = "INFRASTRUCTURE_RESOURCES"
    GOVERNANCE_FINANCE = "GOVERNANCE_FINANCE"
    INSTITUTIONAL_VALUES = "INSTITUTIONAL_VALUES"


class QualityDataQualityStatus(StrEnum):
    EXCELLENT = "EXCELLENT"
    ACCEPTABLE = "ACCEPTABLE"
    WARNING_STALE = "WARNING_STALE"
    WARNING_INCOMPLETE = "WARNING_INCOMPLETE"
    CALCULATION_FAILED = "CALCULATION_FAILED"


class QualityAuditType(StrEnum):
    ACADEMIC_AUDIT = "ACADEMIC_AUDIT"
    ADMINISTRATIVE_AUDIT = "ADMINISTRATIVE_AUDIT"
    GREEN_ENVIRONMENTAL = "GREEN_ENVIRONMENTAL"
    ENERGY_AUDIT = "ENERGY_AUDIT"
    ISO_SURVEILLANCE = "ISO_SURVEILLANCE"
    DEPARTMENT_REVIEW = "DEPARTMENT_REVIEW"


class QualityAuditStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    REPORT_DRAFTED = "REPORT_DRAFTED"
    FINALIZED = "FINALIZED"
    CLOSED = "CLOSED"


class QualityFindingSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QualityFindingStatus(StrEnum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    CLOSED = "CLOSED"
    OVERDUE = "OVERDUE"
    REOPENED = "REOPENED"


class QualityCAPAType(StrEnum):
    CORRECTIVE = "CORRECTIVE"
    PREVENTIVE = "PREVENTIVE"
    IMPROVEMENT = "IMPROVEMENT"


class QualityCAPAStatus(StrEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED_EFFECTIVE = "VERIFIED_EFFECTIVE"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"


class QualityImprovementStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EVALUATING = "EVALUATING"
    ACHIEVED = "ACHIEVED"
    PARTIALLY_ACHIEVED = "PARTIALLY_ACHIEVED"
    CLOSED = "CLOSED"


class AccreditationReadinessCategory(StrEnum):
    HIGH_READINESS = "HIGH_READINESS"
    SUBSTANTIAL_PROGRESS = "SUBSTANTIAL_PROGRESS"
    SIGNIFICANT_GAPS = "SIGNIFICANT_GAPS"
    CRITICAL_REMEDIATION_NEEDED = "CRITICAL_REMEDIATION_NEEDED"


# =============================================================================
# 1. ACCREDITATION FRAMEWORK & VERSION SNAPSHOTS
# =============================================================================


class AccreditationFramework(TenantScopedModel):
    """Configurable accreditation framework (e.g. NAAC, NBA, ISO-21001, Internal IQAC)."""

    __tablename__ = "accreditation_frameworks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_accred_frameworks_tenant_code"),
        Index("idx_accred_frameworks_tenant_status", "tenant_id", "status"),
        Index("idx_accred_frameworks_tenant_type", "tenant_id", "framework_type"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issuing_body: Mapped[str] = mapped_column(String(128), nullable=False)
    framework_type: Mapped[str] = mapped_column(
        String(32), default=AccreditationFrameworkType.CUSTOM, nullable=False
    )
    scope_type: Mapped[str] = mapped_column(String(32), default="INSTITUTION", nullable=False)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AccreditationFrameworkStatus.DRAFT, nullable=False
    )
    current_version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_by_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    scoring_model: Mapped[str] = mapped_column(
        String(32), default=AccreditationScoringModel.NUMERIC_SCALE, nullable=False
    )
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighting_supported: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    versions: Mapped[list["AccreditationFrameworkVersion"]] = relationship(
        "AccreditationFrameworkVersion",
        back_populates="framework",
        cascade="all, delete-orphan",
        order_by="desc(AccreditationFrameworkVersion.version_number)",
    )
    criteria: Mapped[list["AccreditationCriterion"]] = relationship(
        "AccreditationCriterion",
        back_populates="framework",
        cascade="all, delete-orphan",
        order_by="AccreditationCriterion.order_index",
    )
    assessment_cycles: Mapped[list["AccreditationAssessmentCycle"]] = relationship(
        "AccreditationAssessmentCycle",
        back_populates="framework",
        cascade="all, delete-orphan",
    )


class AccreditationFrameworkVersion(TenantScopedModel):
    """Immutable snapshot of an accreditation framework publication."""

    __tablename__ = "accreditation_framework_versions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "framework_id", "version_number", name="uq_accred_framework_versions"
        ),
        Index("idx_accred_framework_ver_fw", "tenant_id", "framework_id"),
    )

    framework_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    criteria_snapshot_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, default=list, nullable=False
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    framework: Mapped["AccreditationFramework"] = relationship(
        "AccreditationFramework", back_populates="versions"
    )


# =============================================================================
# 2. CRITERIA & SUBCRITERIA HIERARCHY
# =============================================================================


class AccreditationCriterion(TenantScopedModel):
    """Criterion or subcriterion within an accreditation framework."""

    __tablename__ = "accreditation_criteria"
    __table_args__ = (
        UniqueConstraint("tenant_id", "framework_id", "code", name="uq_accred_criteria_code"),
        Index("idx_accred_criteria_framework", "tenant_id", "framework_id"),
        Index("idx_accred_criteria_parent", "tenant_id", "parent_criterion_id"),
    )

    framework_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_criterion_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_criteria.id", ondelete="CASCADE"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterion_type: Mapped[str] = mapped_column(
        String(32), default=AccreditationCriterionType.QUALITATIVE, nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assessment_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirements: Mapped[list[str]] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    framework: Mapped["AccreditationFramework"] = relationship(
        "AccreditationFramework", back_populates="criteria"
    )
    parent_criterion: Mapped["AccreditationCriterion | None"] = relationship(
        "AccreditationCriterion", remote_side="AccreditationCriterion.id", back_populates="subcriteria"
    )
    subcriteria: Mapped[list["AccreditationCriterion"]] = relationship(
        "AccreditationCriterion",
        back_populates="parent_criterion",
        cascade="all, delete-orphan",
        order_by="AccreditationCriterion.order_index",
    )
    assessments: Mapped[list["AccreditationCriterionAssessment"]] = relationship(
        "AccreditationCriterionAssessment",
        back_populates="criterion",
        cascade="all, delete-orphan",
    )


# =============================================================================
# 3. ASSESSMENT CYCLES & CRITERION ASSESSMENTS
# =============================================================================


class AccreditationAssessmentCycle(TenantScopedModel):
    """Institutional assessment period or accreditation cycle (e.g. AY 2025-26 NAAC Cycle 2)."""

    __tablename__ = "accreditation_assessment_cycles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "framework_id", "code", name="uq_accred_cycles_code"),
        Index("idx_accred_cycles_tenant_status", "tenant_id", "status"),
    )

    framework_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_submission_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lead_coordinator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    framework: Mapped["AccreditationFramework"] = relationship(
        "AccreditationFramework", back_populates="assessment_cycles"
    )
    criterion_assessments: Mapped[list["AccreditationCriterionAssessment"]] = relationship(
        "AccreditationCriterionAssessment",
        back_populates="cycle",
        cascade="all, delete-orphan",
    )
    readiness_snapshots: Mapped[list["AccreditationReadinessSnapshot"]] = relationship(
        "AccreditationReadinessSnapshot",
        back_populates="cycle",
        cascade="all, delete-orphan",
        order_by="desc(AccreditationReadinessSnapshot.created_at)",
    )


class AccreditationCriterionAssessment(TenantScopedModel):
    """Structured assessment record for a specific criterion in an assessment cycle."""

    __tablename__ = "accreditation_criterion_assessments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "cycle_id", "criterion_id", name="uq_accred_criterion_assessment"
        ),
        Index("idx_accred_crit_assess_cycle", "tenant_id", "cycle_id"),
        Index("idx_accred_crit_assess_status", "tenant_id", "status"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_assessment_cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    criterion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    accountable_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AccreditationAssessmentStatus.UNASSESSED, nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    maturity_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    not_applicable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lock_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    cycle: Mapped["AccreditationAssessmentCycle"] = relationship(
        "AccreditationAssessmentCycle", back_populates="criterion_assessments"
    )
    criterion: Mapped["AccreditationCriterion"] = relationship(
        "AccreditationCriterion", back_populates="assessments"
    )
    evidence_mappings: Mapped[list["AccreditationCriterionEvidenceMap"]] = relationship(
        "AccreditationCriterionEvidenceMap",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


# =============================================================================
# 4. EVIDENCE REPOSITORY & TRACEABILITY
# =============================================================================


class AccreditationEvidence(TenantScopedModel):
    """Institutional evidence record traceable to documents, knowledge items, or records."""

    __tablename__ = "accreditation_evidences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "evidence_code", name="uq_accred_evidence_code"),
        Index("idx_accred_evid_status", "tenant_id", "verification_status"),
        Index("idx_accred_evid_category", "tenant_id", "evidence_category"),
    )

    evidence_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_category: Mapped[str] = mapped_column(
        String(32), default=AccreditationEvidenceCategory.POLICY_SOP, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(32), default="DOCUMENT", nullable=False)
    # Traceable references to core modules
    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documents_records.id", ondelete="SET NULL"), nullable=True
    )
    knowledge_item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="SET NULL"), nullable=True
    )
    record_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("records_registry.id", ondelete="SET NULL"), nullable=True
    )
    external_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidentiality: Mapped[str] = mapped_column(String(32), default="INTERNAL", nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(32), default=AccreditationEvidenceVerificationStatus.UNVERIFIED, nullable=False
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    integrity_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    criterion_mappings: Mapped[list["AccreditationCriterionEvidenceMap"]] = relationship(
        "AccreditationCriterionEvidenceMap",
        back_populates="evidence",
        cascade="all, delete-orphan",
    )


class AccreditationCriterionEvidenceMap(TenantScopedModel):
    """Many-to-many relationship mapping evidence records to criterion assessments."""

    __tablename__ = "accreditation_criterion_evidence_maps"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "assessment_id", "evidence_id", name="uq_accred_crit_evid_map"
        ),
        Index("idx_accred_map_assess", "tenant_id", "assessment_id"),
        Index("idx_accred_map_evid", "tenant_id", "evidence_id"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_criterion_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_evidences.id", ondelete="CASCADE"),
        nullable=False,
    )
    relevance_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapped_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )

    # Relationships
    assessment: Mapped["AccreditationCriterionAssessment"] = relationship(
        "AccreditationCriterionAssessment", back_populates="evidence_mappings"
    )
    evidence: Mapped["AccreditationEvidence"] = relationship(
        "AccreditationEvidence", back_populates="criterion_mappings"
    )


# =============================================================================
# 5. QUALITY INDICATORS (KPIS) & DATA QUALITY VALIDATION
# =============================================================================


class QualityIndicator(TenantScopedModel):
    """Configurable quality indicator/metric for IQAC and accreditation monitoring."""

    __tablename__ = "quality_indicators"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_indicator_code"),
        Index("idx_qi_tenant_category", "tenant_id", "category"),
        Index("idx_qi_tenant_status", "tenant_id", "data_quality_status"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(32), default=QualityIndicatorCategory.ACADEMIC_EXCELLENCE, nullable=False
    )
    source_module: Mapped[str] = mapped_column(String(32), default="ACADEMICS", nullable=False)
    calculation_method: Mapped[str] = mapped_column(Text, nullable=False)
    reporting_frequency: Mapped[str] = mapped_column(String(32), default="ANNUAL", nullable=False)
    unit_of_measurement: Mapped[str] = mapped_column(String(32), default="PERCENTAGE", nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    benchmark_threshold: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_quality_status: Mapped[str] = mapped_column(
        String(32), default=QualityDataQualityStatus.EXCELLENT, nullable=False
    )
    data_quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    observations: Mapped[list["QualityIndicatorObservation"]] = relationship(
        "QualityIndicatorObservation",
        back_populates="indicator",
        cascade="all, delete-orphan",
        order_by="desc(QualityIndicatorObservation.observation_date)",
    )


class QualityIndicatorObservation(TenantScopedModel):
    """Historical time-series observation for a quality indicator."""

    __tablename__ = "quality_indicator_observations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "indicator_id", "period_label", name="uq_qi_obs_period"
        ),
        Index("idx_qi_obs_indicator", "tenant_id", "indicator_id"),
    )

    indicator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quality_indicators.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_label: Mapped[str] = mapped_column(String(64), nullable=False)
    observation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    data_source_mode: Mapped[str] = mapped_column(String(32), default="AUTOMATED_QUERY", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_completeness_pct: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    outlier_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )

    indicator: Mapped["QualityIndicator"] = relationship(
        "QualityIndicator", back_populates="observations"
    )


# =============================================================================
# 6. INTERNAL AUDITS & QUALITY REVIEWS
# =============================================================================


class QualityAuditProgram(TenantScopedModel):
    """Internal Quality Audit program, schedule, and finalized report."""

    __tablename__ = "quality_audit_programs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_audit_code"),
        Index("idx_quality_audit_status", "tenant_id", "status"),
        Index("idx_quality_audit_type", "tenant_id", "audit_type"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    audit_type: Mapped[str] = mapped_column(
        String(32), default=QualityAuditType.ACADEMIC_AUDIT, nullable=False
    )
    scope: Mapped[str] = mapped_column(String(32), default="INSTITUTION_WIDE", nullable=False)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    lead_auditor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    co_auditors_json: Mapped[list[str]] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    scheduled_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_completion_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default=QualityAuditStatus.PLANNED, nullable=False)
    conflict_of_interest_declared: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    summary_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    is_immutable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    checklists: Mapped[list["QualityAuditChecklistItem"]] = relationship(
        "QualityAuditChecklistItem",
        back_populates="audit_program",
        cascade="all, delete-orphan",
        order_by="QualityAuditChecklistItem.order_index",
    )
    findings: Mapped[list["QualityFinding"]] = relationship(
        "QualityFinding",
        back_populates="audit_program",
        cascade="all, delete-orphan",
    )


class QualityAuditChecklistItem(TenantScopedModel):
    """Audit checklist item linked to an audit program and optional framework criterion."""

    __tablename__ = "quality_audit_checklist_items"
    __table_args__ = (
        Index("idx_audit_chk_program", "tenant_id", "audit_program_id"),
    )

    audit_program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quality_audit_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    criterion_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_criteria.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    requirement_description: Mapped[str] = mapped_column(Text, nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(32), default="COMPLIANT", nullable=False)
    auditor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    audit_program: Mapped["QualityAuditProgram"] = relationship(
        "QualityAuditProgram", back_populates="checklists"
    )


# =============================================================================
# 7. FINDINGS & CORRECTIVE ACTIONS (CAPA)
# =============================================================================


class QualityFinding(TenantScopedModel):
    """Institutional finding or compliance gap requiring corrective or preventive action."""

    __tablename__ = "quality_findings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "finding_code", name="uq_quality_finding_code"),
        Index("idx_q_finding_severity", "tenant_id", "severity"),
        Index("idx_q_finding_status", "tenant_id", "status"),
    )

    finding_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="INTERNAL_AUDIT", nullable=False)
    audit_program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quality_audit_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    criterion_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_criteria.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(32), default=QualityFindingSeverity.MEDIUM, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=QualityFindingStatus.OPEN, nullable=False
    )
    identified_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    target_resolution_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    # Relationships
    audit_program: Mapped["QualityAuditProgram | None"] = relationship(
        "QualityAuditProgram", back_populates="findings"
    )
    corrective_actions: Mapped[list["QualityCorrectiveAction"]] = relationship(
        "QualityCorrectiveAction",
        back_populates="finding",
        cascade="all, delete-orphan",
    )


class QualityCorrectiveAction(TenantScopedModel):
    """Corrective and Preventive Action (CAPA) item with separation-of-duties closure verification."""

    __tablename__ = "quality_corrective_actions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "action_code", name="uq_quality_capa_code"),
        Index("idx_q_capa_status", "tenant_id", "status"),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quality_findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_code: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(32), default=QualityCAPAType.CORRECTIVE, nullable=False
    )
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    preventive_measures: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=QualityCAPAStatus.PROPOSED, nullable=False
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documents_records.id", ondelete="SET NULL"), nullable=True
    )
    verification_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    # Separation of duties: action owner cannot verify or close action
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    closure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    finding: Mapped["QualityFinding"] = relationship(
        "QualityFinding", back_populates="corrective_actions"
    )


# =============================================================================
# 8. CONTINUOUS QUALITY IMPROVEMENT (CQI) PLANS
# =============================================================================


class QualityImprovementPlan(TenantScopedModel):
    """Institutional continuous quality improvement initiative and progress tracker."""

    __tablename__ = "quality_improvement_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_improvement_code"),
        Index("idx_q_plan_status", "tenant_id", "status"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_measurement: Mapped[str] = mapped_column(Text, nullable=False)
    target_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    linked_indicator_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("quality_indicators.id", ondelete="SET NULL"), nullable=True
    )
    responsible_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_completion_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=QualityImprovementStatus.DRAFT, nullable=False
    )
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)


# =============================================================================
# 9. ACCREDITATION READINESS SNAPSHOTS & GAP ANALYSIS
# =============================================================================


class AccreditationReadinessSnapshot(TenantScopedModel):
    """Point-in-time calculation snapshot of accreditation readiness and compliance gaps."""

    __tablename__ = "accreditation_readiness_snapshots"
    __table_args__ = (
        Index("idx_accred_readiness_cycle", "tenant_id", "cycle_id"),
        Index("idx_accred_readiness_created", "tenant_id", "created_at"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_assessment_cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    framework_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    criteria_assessed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    criteria_total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_verified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_required_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_high_risk_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_projected: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_maximum: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness_category: Mapped[str] = mapped_column(
        String(32), default=AccreditationReadinessCategory.SIGNIFICANT_GAPS, nullable=False
    )
    gap_summary_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, default=list, nullable=False
    )
    department_readiness_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, default=dict, nullable=False
    )
    calculated_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )

    cycle: Mapped["AccreditationAssessmentCycle"] = relationship(
        "AccreditationAssessmentCycle", back_populates="readiness_snapshots"
    )
