"""Enterprise Privacy & Data Subject Request Fulfillment Engine for CampusOS.

Handles Subject Access Requests (SAR / Access / Export), controlled record corrections,
and GDPR/FERPA/Digital Personal Data Protection aligned anonymization and deletion workflows.
"""

from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.governance_registry import sanitize_dict_for_roles
from app.core.storage import get_document_storage
from app.models.attendance import AttendanceRecord
from app.models.documents import Document
from app.models.examination import SemesterExamResult
from app.models.finance import Invoice, PaymentTransaction
from app.models.governance import (
    PrivacyRequest,
    PrivacyRequestAction,
    PrivacyRequestStatus,
    PrivacyRequestType,
)
from app.models.people import StudentProfile, User
from app.models.placement import PlacementApplication, PlacementOffer
from app.schemas.governance import (
    PrivacyRequestCreate,
    PrivacyRequestReview,
)
from app.services.retention_service import RetentionService

logger = logging.getLogger("campusos.privacy")


# =============================================================================
# DATA PROVIDER REGISTRY
# =============================================================================

class PrivacyDataProviderRegistry:
    """Aggregates data subject records across institutional domains without raw SQL access."""

    @classmethod
    async def gather_subject_data(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        subject_id: UUID,
        target_domains: list[str],
    ) -> dict[str, Any]:
        """Harvests authorized domain snapshots for the identified data subject."""
        domains = [d.lower().strip() for d in target_domains]
        collected: dict[str, Any] = {
            "data_subject_id": str(subject_id),
            "generated_at": datetime.now(UTC).isoformat(),
            "domains": {},
        }

        # 1. People Domain
        if "people" in domains:
            student = await db.scalar(
                select(StudentProfile)
                .options(selectinload(StudentProfile.user))
                .where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.id == subject_id,
                    )
                )
            )
            if student:
                raw_person = {
                    "enrollment_number": student.enrollment_number,
                    "admission_number": student.admission_number,
                    "first_name": student.user.first_name if student.user else None,
                    "last_name": student.user.last_name if student.user else None,
                    "email": student.user.email if student.user else None,
                    "phone_number": student.user.phone_number if student.user else None,
                    "emergency_contact_phone": student.emergency_contact_phone,
                    "status": student.status,
                }
                collected["domains"]["people"] = sanitize_dict_for_roles(raw_person, "StudentProfile")

        # 2. Attendance Domain
        if "attendance" in domains:
            att_records = (await db.execute(
                select(AttendanceRecord).where(
                    and_(
                        AttendanceRecord.tenant_id == tenant_id,
                        AttendanceRecord.student_id == subject_id,
                    )
                ).limit(50)
            )).scalars().all()
            collected["domains"]["attendance"] = {
                "total_records_sampled": len(att_records),
                "summary": [
                    {"status": r.status, "session_id": str(r.session_id)}
                    for r in att_records[:10]
                ],
            }

        # 3. Examinations Domain
        if "examinations" in domains:
            results = (await db.execute(
                select(SemesterExamResult).where(
                    and_(
                        SemesterExamResult.tenant_id == tenant_id,
                        SemesterExamResult.student_id == subject_id,
                    )
                )
            )).scalars().all()
            collected["domains"]["examinations"] = [
                {
                    "semester_id": str(r.semester_id),
                    "gpa": float(r.gpa) if r.gpa is not None else None,
                    "cgpa": float(r.cgpa) if r.cgpa is not None else None,
                    "passed": r.passed,
                }
                for r in results
            ]

        # 4. Finance Domain
        if "finance" in domains:
            invoices = (await db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.tenant_id == tenant_id,
                        Invoice.student_id == subject_id,
                    )
                )
            )).scalars().all()
            collected["domains"]["finance"] = [
                {
                    "invoice_number": inv.invoice_number,
                    "total_amount": float(inv.total_amount),
                    "balance_amount": float(inv.balance_amount),
                    "status": inv.status,
                }
                for inv in invoices
            ]

        # 5. Documents Domain
        if "documents" in domains:
            docs = (await db.execute(
                select(Document).where(
                    and_(
                        Document.tenant_id == tenant_id,
                        Document.owner_user_id == subject_id,
                    )
                )
            )).scalars().all()
            collected["domains"]["documents"] = [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "category": d.category,
                    "verification_status": d.verification_status,
                }
                for d in docs
            ]

        return collected


# =============================================================================
# ANONYMIZATION SERVICE
# =============================================================================

class AnonymizationService:
    """Anonymizes personal identifiers while preserving institutional audit and academic credits."""

    @classmethod
    async def anonymize_student(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        actor_id: UUID | None = None,
    ) -> None:
        student = await db.scalar(
            select(StudentProfile)
            .options(selectinload(StudentProfile.user))
            .where(
                and_(
                    StudentProfile.tenant_id == tenant_id,
                    StudentProfile.id == student_id,
                )
            )
        )
        if not student:
            return

        now = datetime.now(UTC)
        anon_tag = f"anon_{student.id.hex[:6]}"

        # Anonymize user record
        if student.user:
            student.user.first_name = "Anonymous"
            student.user.last_name = f"Student {anon_tag}"
            student.user.email = f"{anon_tag}@campusos.internal"
            student.user.phone_number = None
            student.user.status = "SUSPENDED"

        # Anonymize profile personal attributes
        student.emergency_contact_phone = None
        student.address_line1 = "[ANONYMIZED_REGION]"
        student.status = "ANONYMIZED"
        student.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DATA_ANONYMIZE,
                entity_type="StudentProfile",
                entity_id=student.id,
                user_id=actor_id,
                new_values_json={"status": "ANONYMIZED", "tag": anon_tag},
            )
        )
        await db.commit()
        logger.info("Anonymized student profile %s for tenant %s", student_id, tenant_id)


# =============================================================================
# PRIVACY SERVICE
# =============================================================================

class PrivacyService:
    """Orchestrates privacy request lifecycle from submission through verified fulfillment."""

    @classmethod
    async def submit_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: PrivacyRequestCreate,
        actor_id: UUID,
    ) -> PrivacyRequest:
        """Submit a formal privacy or data subject request."""
        now = datetime.now(UTC)
        req_number = f"PRV-{now.strftime('%Y%m')}-{uuid4().hex[:6].upper()}"

        req = PrivacyRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            request_number=req_number,
            request_type=payload.request_type.upper(),
            status=PrivacyRequestStatus.SUBMITTED,
            data_subject_type=payload.data_subject_type.upper(),
            data_subject_id=payload.data_subject_id,
            requested_by_user_id=actor_id,
            description=payload.description,
            target_domains_json=payload.target_domains,
            payload_json=payload.payload,
            created_at=now,
            updated_at=now,
        )
        db.add(req)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.PRIVACY_REQUEST,
                entity_type="PrivacyRequest",
                entity_id=req.id,
                user_id=actor_id,
                new_values_json={"request_number": req_number, "type": req.request_type, "status": req.status},
            )
        )

        await db.commit()
        await db.refresh(req)
        logger.info("Submitted privacy request %s for tenant %s", req.request_number, tenant_id)
        return req

    @classmethod
    async def get_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
    ) -> PrivacyRequest:
        """Retrieve privacy request with all actions."""
        stmt = (
            select(PrivacyRequest)
            .options(selectinload(PrivacyRequest.actions))
            .where(
                and_(
                    PrivacyRequest.id == request_id,
                    PrivacyRequest.tenant_id == tenant_id,
                )
            )
        )
        req = (await db.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundException("PrivacyRequest", request_id)
        return req

    @classmethod
    async def list_requests(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        request_type: str | None = None,
    ) -> list[PrivacyRequest]:
        """List privacy requests in tenant."""
        stmt = (
            select(PrivacyRequest)
            .options(selectinload(PrivacyRequest.actions))
            .where(
                and_(
                    PrivacyRequest.tenant_id == tenant_id,
                    PrivacyRequest.status == status if status else True,
                    PrivacyRequest.request_type == request_type.upper() if request_type else True,
                )
            )
            .order_by(PrivacyRequest.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def review_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        payload: PrivacyRequestReview,
        reviewer_id: UUID,
    ) -> PrivacyRequest:
        """Approve or reject a submitted privacy request with evidence."""
        req = await cls.get_request(db, tenant_id, request_id)
        stat = payload.status.upper().strip()

        if stat not in (PrivacyRequestStatus.APPROVED, PrivacyRequestStatus.REJECTED):
            raise ValidationException("Review status must be either 'APPROVED' or 'REJECTED'.")

        now = datetime.now(UTC)
        req.status = stat
        req.reviewed_by_user_id = reviewer_id
        req.evidence_notes = payload.evidence_notes
        req.rejection_reason = payload.rejection_reason if stat == PrivacyRequestStatus.REJECTED else None
        req.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.PRIVACY_REQUEST,
                entity_type="PrivacyRequest",
                entity_id=req.id,
                user_id=reviewer_id,
                new_values_json={"status": stat, "rejection_reason": req.rejection_reason},
            )
        )

        await db.commit()
        await db.refresh(req)
        return req

    @classmethod
    async def execute_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        actor_id: UUID,
    ) -> PrivacyRequest:
        """Executes an approved privacy request (Export generation, Correction, or Deletion)."""
        req = await cls.get_request(db, tenant_id, request_id)

        if req.status != PrivacyRequestStatus.APPROVED:
            raise ConflictException(f"Privacy request must be 'APPROVED' before execution (currently '{req.status}').")

        req.status = PrivacyRequestStatus.IN_PROGRESS
        now = datetime.now(UTC)

        if req.request_type in (PrivacyRequestType.ACCESS, PrivacyRequestType.EXPORT):
            # Gather subject data from registered providers
            data = await PrivacyDataProviderRegistry.gather_subject_data(
                db=db,
                tenant_id=tenant_id,
                subject_id=req.data_subject_id,
                target_domains=req.target_domains_json,
            )
            content_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
            dest_key = f"tenants/{tenant_id}/privacy/{req.id}/subject_export_{now.strftime('%Y%m%d_%H%M%S')}.json"

            storage = get_document_storage()
            await storage.upload(
                file_content=content_bytes,
                destination_key=dest_key,
                mime_type="application/json",
                metadata={"tenant_id": str(tenant_id), "request_id": str(req.id)},
            )

            req.export_storage_key = dest_key
            req.export_expires_at = now + timedelta(days=7)
            req.status = PrivacyRequestStatus.COMPLETED
            req.completed_at = now

            action_rec = PrivacyRequestAction(
                id=uuid4(),
                tenant_id=tenant_id,
                request_id=req.id,
                action_type="EXPORT",
                domain="GLOBAL",
                entity_type="SubjectDataPackage",
                entity_id=req.data_subject_id,
                status="APPLIED",
                performed_by_user_id=actor_id,
                performed_at=now,
            )
            db.add(action_rec)

            db.add(
                build_audit_entry(
                    tenant_id=tenant_id,
                    action=AuditEventCategory.DATA_EXPORT,
                    entity_type="PrivacyRequest",
                    entity_id=req.id,
                    user_id=actor_id,
                    new_values_json={"export_key": dest_key, "size_bytes": len(content_bytes)},
                )
            )

        elif req.request_type == PrivacyRequestType.CORRECTION:
            # Controlled correction workflow
            student = await db.scalar(
                select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.id == req.data_subject_id,
                    )
                )
            )
            if not student:
                raise NotFoundException("StudentProfile", req.data_subject_id)

            changes = req.payload_json or {}
            old_vals: dict[str, Any] = {}
            new_vals: dict[str, Any] = {}

            if "emergency_contact_phone" in changes:
                old_vals["emergency_contact_phone"] = student.emergency_contact_phone
                student.emergency_contact_phone = str(changes["emergency_contact_phone"]).strip()
                new_vals["emergency_contact_phone"] = student.emergency_contact_phone

            if "address_line1" in changes:
                old_vals["address_line1"] = student.address_line1
                student.address_line1 = str(changes["address_line1"]).strip()
                new_vals["address_line1"] = student.address_line1

            req.status = PrivacyRequestStatus.COMPLETED
            req.completed_at = now

            action_rec = PrivacyRequestAction(
                id=uuid4(),
                tenant_id=tenant_id,
                request_id=req.id,
                action_type="MUTATE",
                domain="people",
                entity_type="StudentProfile",
                entity_id=student.id,
                status="APPLIED",
                old_values_json=old_vals,
                new_values_json=new_vals,
                performed_by_user_id=actor_id,
                performed_at=now,
            )
            db.add(action_rec)

            db.add(
                build_audit_entry(
                    tenant_id=tenant_id,
                    action=AuditEventCategory.DATA_MODIFY,
                    entity_type="StudentProfile",
                    entity_id=student.id,
                    user_id=actor_id,
                    old_values_json=old_vals,
                    new_values_json=new_vals,
                )
            )

        elif req.request_type in (PrivacyRequestType.DELETION, PrivacyRequestType.RESTRICTION):
            # Check legal hold & retention safeguards
            ret_eval = await RetentionService.evaluate_retention(
                db=db,
                tenant_id=tenant_id,
                resource_type="students",
                resource_id=req.data_subject_id,
            )
            if ret_eval.decision == "BLOCKED":
                req.status = PrivacyRequestStatus.PARTIALLY_COMPLETED
                req.completed_at = now

                action_rec = PrivacyRequestAction(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    request_id=req.id,
                    action_type="DELETE",
                    domain="people",
                    entity_type="StudentProfile",
                    entity_id=req.data_subject_id,
                    status="BLOCKED",
                    blocked_reason=ret_eval.blocked_reason,
                    performed_by_user_id=actor_id,
                    performed_at=now,
                )
                db.add(action_rec)
            else:
                await AnonymizationService.anonymize_student(
                    db=db,
                    tenant_id=tenant_id,
                    student_id=req.data_subject_id,
                    actor_id=actor_id,
                )
                req.status = PrivacyRequestStatus.COMPLETED
                req.completed_at = now

                action_rec = PrivacyRequestAction(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    request_id=req.id,
                    action_type="ANONYMIZE",
                    domain="people",
                    entity_type="StudentProfile",
                    entity_id=req.data_subject_id,
                    status="APPLIED",
                    performed_by_user_id=actor_id,
                    performed_at=now,
                )
                db.add(action_rec)

        req.updated_at = now
        await db.commit()
        return await cls.get_request(db, tenant_id, request_id)

    @classmethod
    async def get_privacy_export_file(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        actor_id: UUID,
    ) -> tuple[bytes, str]:
        """Download secured privacy export artifact ensuring tenant isolation and expiry."""
        req = await cls.get_request(db, tenant_id, request_id)
        if not req.export_storage_key:
            raise NotFoundException("PrivacyExportArtifact", request_id)

        now = datetime.now(UTC)
        if req.export_expires_at:
            exp = req.export_expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if now > exp:
                raise ValidationException("The requested privacy export artifact has expired and is no longer available.")

        storage = get_document_storage()
        storage.validate_tenant_storage_key(req.export_storage_key, tenant_id)
        content = await storage.download(req.export_storage_key)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DATA_DOWNLOAD,
                entity_type="PrivacyExport",
                entity_id=req.id,
                user_id=actor_id,
            )
        )
        await db.commit()

        filename = f"privacy_export_{req.request_number}.json"
        return content, filename
