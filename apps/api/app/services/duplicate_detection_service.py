"""Duplicate Detection Service & Candidate Matching Framework (Step 24).

Implements deterministic matching algorithms across governed master entities
(Student, Company, Department) utilizing normalized signal comparisons.
Generates auditable DuplicateCandidate pairs for review.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    DuplicateCandidateAlreadyResolvedException,
    DuplicateCandidateNotFoundException,
)
from app.models.core import Department
from app.models.master_data import (
    DuplicateCandidate,
    DuplicateStatus,
    MasterDataType,
)
from app.models.people import StudentProfile
from app.models.placement import Company
from app.repositories.master_data_repository import MasterDataRepository
from app.services.normalization_service import NormalizationService


class DuplicateDetectionService:
    """Detects duplicate candidates across governed institutional entities."""

    MATCH_THRESHOLD = 70.0

    @classmethod
    async def detect_duplicates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str,
        limit: int = 50,
    ) -> list[DuplicateCandidate]:
        """Scan active records in a tenant and record duplicate candidate pairs."""
        m_type = master_type.upper()
        repo = MasterDataRepository(db)
        candidates_found: list[DuplicateCandidate] = []

        if m_type == MasterDataType.STUDENT:
            candidates_found = await cls._detect_student_duplicates(db, tenant_id, repo, limit)
        elif m_type == MasterDataType.COMPANY:
            candidates_found = await cls._detect_company_duplicates(db, tenant_id, repo, limit)
        elif m_type == MasterDataType.DEPARTMENT:
            candidates_found = await cls._detect_department_duplicates(db, tenant_id, repo, limit)

        return candidates_found

    scan_duplicates_for_type = detect_duplicates

    @classmethod
    async def _detect_student_duplicates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        repo: MasterDataRepository,
        limit: int,
    ) -> list[DuplicateCandidate]:
        stmt = (
            select(StudentProfile)
            .where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.status != "MERGED",
            )
            .options(selectinload(StudentProfile.user))
            .limit(200)
        )
        res = await db.execute(stmt)
        students = list(res.scalars().all())

        new_candidates: list[DuplicateCandidate] = []
        n = len(students)

        for i in range(n):
            if len(new_candidates) >= limit:
                break
            s1 = students[i]
            s1_adm = NormalizationService.normalize_code(s1.admission_number)
            s1_reg = NormalizationService.normalize_code(s1.registration_number)
            s1_email = NormalizationService.normalize_email(s1.user.email if s1.user else "")
            s1_phone = NormalizationService.normalize_phone(s1.user.phone_number if s1.user else "")
            s1_name = NormalizationService.normalize_text(
                f"{s1.user.first_name} {s1.user.last_name}" if s1.user else ""
            )

            for j in range(i + 1, n):
                if len(new_candidates) >= limit:
                    break
                s2 = students[j]
                s2_adm = NormalizationService.normalize_code(s2.admission_number)
                s2_reg = NormalizationService.normalize_code(s2.registration_number)
                s2_email = NormalizationService.normalize_email(s2.user.email if s2.user else "")
                s2_phone = NormalizationService.normalize_phone(
                    s2.user.phone_number if s2.user else ""
                )
                s2_name = NormalizationService.normalize_text(
                    f"{s2.user.first_name} {s2.user.last_name}" if s2.user else ""
                )

                score = 0.0
                reasons: list[str] = []

                # Exact admission number
                if s1_adm and s2_adm and s1_adm == s2_adm:
                    score = max(score, 100.0)
                    reasons.append("identical_admission_number")

                # Exact registration number
                if s1_reg and s2_reg and s1_reg == s2_reg:
                    score = max(score, 100.0)
                    reasons.append("identical_registration_number")

                # Matching email
                if s1_email and s2_email and s1_email == s2_email:
                    score = max(score, 90.0)
                    reasons.append("matching_email")

                # Matching full name + DOB
                if (
                    s1_name
                    and s2_name
                    and s1_name == s2_name
                    and s1.date_of_birth == s2.date_of_birth
                ):
                    score = max(score, 85.0)
                    reasons.append("matching_name_and_dob")

                # Matching phone
                if s1_phone and s2_phone and s1_phone == s2_phone:
                    score = max(score, 75.0)
                    reasons.append("matching_phone_number")

                if score >= cls.MATCH_THRESHOLD:
                    existing = await repo.get_duplicate_candidate_by_pair(
                        tenant_id, MasterDataType.STUDENT, s1.id, s2.id
                    )
                    if not existing:
                        cand = DuplicateCandidate(
                            tenant_id=tenant_id,
                            master_type=MasterDataType.STUDENT,
                            record_a_id=s1.id,
                            record_b_id=s2.id,
                            match_score=score,
                            match_reasons=reasons,
                            status=DuplicateStatus.PENDING,
                        )
                        await repo.create_duplicate_candidate(cand)
                        new_candidates.append(cand)

        return new_candidates

    @classmethod
    async def _detect_company_duplicates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        repo: MasterDataRepository,
        limit: int,
    ) -> list[DuplicateCandidate]:
        stmt = (
            select(Company)
            .where(
                Company.tenant_id == tenant_id,
                Company.status != "MERGED",
            )
            .limit(200)
        )
        res = await db.execute(stmt)
        companies = list(res.scalars().all())

        new_candidates: list[DuplicateCandidate] = []
        n = len(companies)

        for i in range(n):
            if len(new_candidates) >= limit:
                break
            c1 = companies[i]
            c1_name = NormalizationService.normalize_text(c1.name)
            c1_dom = NormalizationService.normalize_domain(c1.website)

            for j in range(i + 1, n):
                if len(new_candidates) >= limit:
                    break
                c2 = companies[j]
                c2_name = NormalizationService.normalize_text(c2.name)
                c2_dom = NormalizationService.normalize_domain(c2.website)

                score = 0.0
                reasons: list[str] = []

                if c1_name and c2_name and c1_name == c2_name:
                    score = max(score, 95.0)
                    reasons.append("matching_company_name")

                if c1_dom and c2_dom and c1_dom == c2_dom:
                    score = max(score, 90.0)
                    reasons.append("matching_website_domain")

                if score >= cls.MATCH_THRESHOLD:
                    existing = await repo.get_duplicate_candidate_by_pair(
                        tenant_id, MasterDataType.COMPANY, c1.id, c2.id
                    )
                    if not existing:
                        cand = DuplicateCandidate(
                            tenant_id=tenant_id,
                            master_type=MasterDataType.COMPANY,
                            record_a_id=c1.id,
                            record_b_id=c2.id,
                            match_score=score,
                            match_reasons=reasons,
                            status=DuplicateStatus.PENDING,
                        )
                        await repo.create_duplicate_candidate(cand)
                        new_candidates.append(cand)

        return new_candidates

    @classmethod
    async def _detect_department_duplicates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        repo: MasterDataRepository,
        limit: int,
    ) -> list[DuplicateCandidate]:
        stmt = (
            select(Department)
            .where(
                Department.tenant_id == tenant_id,
                Department.is_active == True,  # noqa: E712
            )
            .limit(200)
        )
        res = await db.execute(stmt)
        depts = list(res.scalars().all())

        new_candidates: list[DuplicateCandidate] = []
        n = len(depts)

        for i in range(n):
            if len(new_candidates) >= limit:
                break
            d1 = depts[i]
            d1_code = NormalizationService.normalize_code(d1.code)
            d1_name = NormalizationService.normalize_text(d1.name)

            for j in range(i + 1, n):
                if len(new_candidates) >= limit:
                    break
                d2 = depts[j]
                d2_code = NormalizationService.normalize_code(d2.code)
                d2_name = NormalizationService.normalize_text(d2.name)

                score = 0.0
                reasons: list[str] = []

                if d1_code and d2_code and d1_code == d2_code:
                    score = max(score, 100.0)
                    reasons.append("identical_department_code")

                if d1_name and d2_name and d1_name == d2_name and d1.campus_id == d2.campus_id:
                    score = max(score, 90.0)
                    reasons.append("matching_department_name_and_campus")

                if score >= cls.MATCH_THRESHOLD:
                    existing = await repo.get_duplicate_candidate_by_pair(
                        tenant_id, MasterDataType.DEPARTMENT, d1.id, d2.id
                    )
                    if not existing:
                        cand = DuplicateCandidate(
                            tenant_id=tenant_id,
                            master_type=MasterDataType.DEPARTMENT,
                            record_a_id=d1.id,
                            record_b_id=d2.id,
                            match_score=score,
                            match_reasons=reasons,
                            status=DuplicateStatus.PENDING,
                        )
                        await repo.create_duplicate_candidate(cand)
                        new_candidates.append(cand)

        return new_candidates

    @classmethod
    async def review_candidate(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        candidate_id: UUID,
        status: DuplicateStatus,
        reviewer_id: UUID | None = None,
        notes: str | None = None,
    ) -> DuplicateCandidate:
        """Steward decision resolving a duplicate candidate pair."""
        repo = MasterDataRepository(db)
        cand = await repo.get_duplicate_candidate(candidate_id, tenant_id)
        if not cand:
            raise DuplicateCandidateNotFoundException(str(candidate_id))

        if cand.status not in [DuplicateStatus.PENDING, DuplicateStatus.CONFIRMED_DUPLICATE]:
            raise DuplicateCandidateAlreadyResolvedException(str(candidate_id), cand.status)

        cand.status = status
        cand.reviewed_by = reviewer_id
        cand.reviewed_at = datetime.now(UTC)
        cand.review_notes = notes

        # Audit
        action = (
            AuditEventCategory.DUPLICATE_CONFIRMED
            if status == DuplicateStatus.CONFIRMED_DUPLICATE
            else AuditEventCategory.DUPLICATE_DISMISSED
        )
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=action,
            entity_type="duplicate_candidate",
            entity_id=cand.id,
            user_id=reviewer_id,
            business_context=(
                f"Candidate {candidate_id} marked as {status} for {cand.master_type}."
            ),
        )
        db.add(audit)
        await db.flush()

        return cand
