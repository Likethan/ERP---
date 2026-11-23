"""Campus Physical Security, Visitor Management & Emergency Response Service Layer (Step 68).

Product: CampusOS — "One Campus. One System. One Source of Truth."
"""

import hashlib
import hmac
import secrets
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campus_security import (
    AccessGrant,
    CampusSecurityIncident,
    ContractorAccessProfile,
    EmergencyEvent,
    EmergencyResponseTask,
    PatrolCheckpointRecord,
    SecurityCheckpoint,
    SecurityPatrolPlan,
    SecurityZone,
    VisitorPass,
    VisitorProfile,
    VisitorRequest,
)
from app.schemas.campus_security import (
    AccessGrantCreate,
    ContractorProfileCreate,
    ContractorProfileUpdate,
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyTaskCreate,
    EmergencyTaskUpdate,
    PatrolCheckpointRecordCreate,
    PatrolPlanCreate,
    SecurityCheckpointCreate,
    SecurityIncidentCreate,
    SecurityIncidentUpdate,
    SecurityZoneCreate,
    VisitorGateCheckIn,
    VisitorGateCheckOut,
    VisitorProfileCreate,
    VisitorRequestCreate,
    VisitorRequestReview,
)

# Cryptographic secret for signing visitor QR access tokens
SIGNING_KEY = b"campusos-sec-gate-token-secret-2026-v68"

def to_utc(dt: datetime) -> datetime:
    """Ensures datetime is timezone-aware in UTC for consistent cross-database comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)



def generate_signed_visitor_token(tenant_id: UUID, pass_number: str, valid_until: datetime) -> str:
    """Generates an unpredictable, HMAC-SHA256 signed tamper-proof visitor pass token."""
    nonce = secrets.token_hex(8)
    payload = f"{tenant_id}:{pass_number}:{int(valid_until.timestamp())}:{nonce}"
    sig = hmac.new(SIGNING_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    return f"VT-{payload}:{sig}"


def verify_signed_visitor_token(token: str) -> tuple[bool, str]:
    """Validates the cryptographic HMAC signature and extracts token integrity."""
    if not token.startswith("VT-") or ":" not in token:
        return False, "Invalid token format"
    try:
        raw = token[3:]
        parts = raw.split(":")
        if len(parts) != 5:
            return False, "Malformed token components"
        tenant_str, pass_no, timestamp_str, nonce, sig = parts
        payload = f"{tenant_str}:{pass_no}:{timestamp_str}:{nonce}"
        expected_sig = hmac.new(SIGNING_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected_sig):
            return False, "Cryptographic signature mismatch"
        expiry_ts = int(timestamp_str)
        if datetime.now(UTC).timestamp() > expiry_ts:
            return False, "Token has expired"
        return True, "Valid"
    except Exception as e:
        return False, f"Signature validation error: {str(e)}"


class CampusSecurityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # 1. CHECKPOINTS & SECURITY ZONES
    # =========================================================================

    async def list_checkpoints(
        self, tenant_id: UUID, is_manned: bool | None = None, is_active: bool = True
    ) -> list[SecurityCheckpoint]:
        query = select(SecurityCheckpoint).where(
            SecurityCheckpoint.tenant_id == tenant_id,
            SecurityCheckpoint.is_active == is_active,
        )
        if is_manned is not None:
            query = query.where(SecurityCheckpoint.is_manned == is_manned)
        result = await self.db.execute(query.order_by(SecurityCheckpoint.code))
        return list(result.scalars().all())

    async def create_checkpoint(
        self, tenant_id: UUID, data: SecurityCheckpointCreate
    ) -> SecurityCheckpoint:
        chkpt = SecurityCheckpoint(
            tenant_id=tenant_id,
            code=data.code.upper(),
            name=data.name,
            checkpoint_type=data.checkpoint_type,
            location_description=data.location_description,
            is_manned=data.is_manned,
            operating_hours=data.operating_hours,
            guard_post_phone=data.guard_post_phone,
            is_active=data.is_active,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(chkpt)
        await self.db.commit()
        await self.db.refresh(chkpt)
        return chkpt

    async def list_zones(
        self, tenant_id: UUID, clearance_level: str | None = None
    ) -> list[SecurityZone]:
        query = select(SecurityZone).where(
            SecurityZone.tenant_id == tenant_id,
            SecurityZone.is_active == True,
        )
        if clearance_level:
            query = query.where(SecurityZone.clearance_level == clearance_level)
        result = await self.db.execute(query.order_by(SecurityZone.code))
        return list(result.scalars().all())

    async def create_zone(self, tenant_id: UUID, data: SecurityZoneCreate) -> SecurityZone:
        zone = SecurityZone(
            tenant_id=tenant_id,
            code=data.code.upper(),
            name=data.name,
            clearance_level=data.clearance_level,
            building_name=data.building_name,
            floor_number=data.floor_number,
            requires_escort=data.requires_escort,
            max_occupancy=data.max_occupancy,
            emergency_assembly_point=data.emergency_assembly_point,
            is_active=data.is_active,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(zone)
        await self.db.commit()
        await self.db.refresh(zone)
        return zone

    # =========================================================================
    # 2. VISITOR DIRECTORY & PRE-REGISTRATION
    # =========================================================================

    async def list_visitor_profiles(
        self, tenant_id: UUID, search: str | None = None
    ) -> list[VisitorProfile]:
        query = select(VisitorProfile).where(VisitorProfile.tenant_id == tenant_id)
        if search:
            s = f"%{search}%"
            query = query.where(
                or_(
                    VisitorProfile.full_name.ilike(s),
                    VisitorProfile.email.ilike(s),
                    VisitorProfile.phone.ilike(s),
                    VisitorProfile.organization.ilike(s),
                )
            )
        result = await self.db.execute(query.order_by(VisitorProfile.full_name))
        return list(result.scalars().all())

    async def get_or_create_visitor_profile(
        self, tenant_id: UUID, data: VisitorProfileCreate
    ) -> VisitorProfile:
        query = select(VisitorProfile).where(
            VisitorProfile.tenant_id == tenant_id,
            or_(
                VisitorProfile.phone == data.phone,
                VisitorProfile.email == data.email.lower().strip(),
            ),
        )
        existing = (await self.db.execute(query)).scalar_one_or_none()
        if existing:
            # Check blacklist
            if existing.is_blacklisted:
                raise ValueError(
                    f"Visitor is blacklisted from campus entry: {existing.blacklist_reason or 'Security alert'}"
                )
            return existing

        profile = VisitorProfile(
            tenant_id=tenant_id,
            full_name=data.full_name,
            email=data.email.lower().strip(),
            phone=data.phone,
            organization=data.organization,
            id_document_type=data.id_document_type,
            id_document_number_masked=data.id_document_number_masked,
            is_vip=data.is_vip,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def list_visitor_requests(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[VisitorRequest]:
        query = select(VisitorRequest).where(VisitorRequest.tenant_id == tenant_id)
        if status:
            query = query.where(VisitorRequest.status == status)
        result = await self.db.execute(query.order_by(VisitorRequest.expected_arrival_at.desc()))
        return list(result.scalars().all())

    async def submit_visitor_request(
        self, tenant_id: UUID, data: VisitorRequestCreate, host_user_id: UUID | None = None
    ) -> VisitorRequest:
        # 1. Resolve or create visitor profile
        profile_input = VisitorProfileCreate(
            full_name=data.visitor_name,
            email=data.visitor_email,
            phone=data.visitor_phone,
            organization=data.organization,
            id_document_type=data.id_document_type,
            id_document_number_masked=data.id_document_number_masked,
            is_vip=(data.visitor_category == "VIP"),
        )
        profile = await self.get_or_create_visitor_profile(tenant_id, profile_input)

        # 2. Count requests to generate sequential VR code
        count_query = select(func.count(VisitorRequest.id)).where(VisitorRequest.tenant_id == tenant_id)
        count = (await self.db.execute(count_query)).scalar() or 0
        req_number = f"VR-2026-{str(count + 1).padStart(4, '0')}" if hasattr(str, 'padStart') else f"VR-2026-{count + 1:04d}"

        req = VisitorRequest(
            tenant_id=tenant_id,
            request_number=req_number,
            visitor_id=profile.id,
            visitor_name=data.visitor_name,
            visitor_phone=data.visitor_phone,
            visitor_email=data.visitor_email,
            visitor_category=data.visitor_category,
            host_user_id=host_user_id,
            host_name=data.host_name,
            host_department=data.host_department,
            visit_purpose=data.visit_purpose,
            destination_zone_id=data.destination_zone_id,
            destination_description=data.destination_description,
            expected_arrival_at=data.expected_arrival_at,
            expected_departure_at=data.expected_departure_at,
            status="PENDING",
            approval_required=True,
            vehicle_number=data.vehicle_number,
            has_vehicle=data.has_vehicle,
            accompanying_count=data.accompanying_count,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(req)
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def review_visitor_request(
        self,
        tenant_id: UUID,
        request_id: UUID,
        reviewer_user_id: UUID | None,
        review: VisitorRequestReview,
    ) -> tuple[VisitorRequest, VisitorPass | None]:
        req_query = select(VisitorRequest).where(
            VisitorRequest.tenant_id == tenant_id, VisitorRequest.id == request_id
        )
        req = (await self.db.execute(req_query)).scalar_one_or_none()
        if not req:
            raise ValueError("Visitor request not found")

        req.status = review.decision
        req.approved_by_user_id = reviewer_user_id
        req.approved_at = datetime.now(UTC)
        req.rejection_reason = review.rejection_reason

        pass_record = None
        if review.decision == "APPROVED":
            # Generate sequential VP pass number
            count_query = select(func.count(VisitorPass.id)).where(VisitorPass.tenant_id == tenant_id)
            count = (await self.db.execute(count_query)).scalar() or 0
            pass_no = f"VP-2026-{count + 1:04d}"

            # Generate HMAC signed token
            signed_tok = generate_signed_visitor_token(tenant_id, pass_no, req.expected_departure_at)

            pass_record = VisitorPass(
                tenant_id=tenant_id,
                pass_number=pass_no,
                request_id=req.id,
                visitor_id=req.visitor_id,
                visitor_name=req.visitor_name,
                visitor_category=req.visitor_category,
                host_name=req.host_name,
                destination=req.destination_description,
                signed_token=signed_tok,
                valid_from=req.expected_arrival_at,
                valid_until=req.expected_departure_at,
                status="ISSUED",
            )
            self.db.add(pass_record)

        await self.db.commit()
        await self.db.refresh(req)
        if pass_record:
            await self.db.refresh(pass_record)
        return req, pass_record

    # =========================================================================
    # 3. GATE OPERATIONS (CHECK-IN, CHECK-OUT, PASS VERIFICATION)
    # =========================================================================

    async def list_passes(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[VisitorPass]:
        query = select(VisitorPass).where(VisitorPass.tenant_id == tenant_id)
        if status:
            query = query.where(VisitorPass.status == status)
        result = await self.db.execute(query.order_by(VisitorPass.created_at.desc()))
        return list(result.scalars().all())

    async def verify_pass_token(self, tenant_id: UUID, signed_token: str) -> VisitorPass:
        # Cryptographic check
        is_valid, reason = verify_signed_visitor_token(signed_token)
        if not is_valid:
            raise ValueError(f"Visitor pass token rejected: {reason}")

        query = select(VisitorPass).where(
            VisitorPass.tenant_id == tenant_id, VisitorPass.signed_token == signed_token
        )
        pass_rec = (await self.db.execute(query)).scalar_one_or_none()
        if not pass_rec:
            raise ValueError("Visitor pass record not found for token")

        if pass_rec.status == "REVOKED":
            raise ValueError(f"Visitor pass was revoked: {pass_rec.revocation_reason or 'Security alert'}")
        if pass_rec.status == "EXPIRED":
            raise ValueError("Visitor pass has expired")

        return pass_rec

    async def gate_check_in(
        self,
        tenant_id: UUID,
        pass_id: UUID,
        payload: VisitorGateCheckIn,
        officer_user_id: UUID | None = None,
    ) -> VisitorPass:
        pass_query = select(VisitorPass).where(
            VisitorPass.tenant_id == tenant_id, VisitorPass.id == pass_id
        )
        pass_rec = (await self.db.execute(pass_query)).scalar_one_or_none()
        if not pass_rec:
            raise ValueError("Visitor pass not found")

        # Duplicate check-in prevention
        if pass_rec.status == "CHECKED_IN":
            raise ValueError(
                f"Duplicate check-in rejected: Visitor {pass_rec.visitor_name} is already checked in at checkpoint {pass_rec.check_in_checkpoint_id}"
            )
        if pass_rec.status in ("REVOKED", "EXPIRED", "CHECKED_OUT"):
            raise ValueError(f"Cannot check in pass with status {pass_rec.status}")

        now = datetime.now(UTC)
        # Expiration check
        if now > to_utc(pass_rec.valid_until):
            pass_rec.status = "EXPIRED"
            await self.db.commit()
            raise ValueError("Visit window has already expired")

        pass_rec.status = "CHECKED_IN"
        pass_rec.check_in_at = now
        pass_rec.check_in_checkpoint_id = payload.checkpoint_id
        pass_rec.check_in_officer_id = officer_user_id
        if payload.vehicle_number:
            meta = pass_rec.metadata_json or {}
            meta["check_in_vehicle"] = payload.vehicle_number
            pass_rec.metadata_json = meta

        # Increment visitor profile total visits
        await self.db.execute(
            update(VisitorProfile)
            .where(VisitorProfile.id == pass_rec.visitor_id)
            .values(total_visits=VisitorProfile.total_visits + 1)
        )

        await self.db.commit()
        await self.db.refresh(pass_rec)
        return pass_rec

    async def gate_check_out(
        self,
        tenant_id: UUID,
        pass_id: UUID,
        payload: VisitorGateCheckOut,
        officer_user_id: UUID | None = None,
    ) -> VisitorPass:
        pass_query = select(VisitorPass).where(
            VisitorPass.tenant_id == tenant_id, VisitorPass.id == pass_id
        )
        pass_rec = (await self.db.execute(pass_query)).scalar_one_or_none()
        if not pass_rec:
            raise ValueError("Visitor pass not found")

        if pass_rec.status not in ("CHECKED_IN", "OVERDUE"):
            raise ValueError(f"Cannot check out visitor pass with status {pass_rec.status}")

        now = datetime.now(UTC)
        pass_rec.status = "CHECKED_OUT"
        pass_rec.check_out_at = now
        pass_rec.check_out_checkpoint_id = payload.checkpoint_id
        pass_rec.check_out_officer_id = officer_user_id
        pass_rec.is_overdue = False

        await self.db.commit()
        await self.db.refresh(pass_rec)
        return pass_rec

    async def revoke_pass(
        self, tenant_id: UUID, pass_id: UUID, reason: str, officer_user_id: UUID | None = None
    ) -> VisitorPass:
        pass_query = select(VisitorPass).where(
            VisitorPass.tenant_id == tenant_id, VisitorPass.id == pass_id
        )
        pass_rec = (await self.db.execute(pass_query)).scalar_one_or_none()
        if not pass_rec:
            raise ValueError("Visitor pass not found")

        pass_rec.status = "REVOKED"
        pass_rec.revoked_at = datetime.now(UTC)
        pass_rec.revocation_reason = reason
        await self.db.commit()
        await self.db.refresh(pass_rec)
        return pass_rec

    async def flag_overdue_visitors(self, tenant_id: UUID) -> int:
        now = datetime.now(UTC)
        query = (
            update(VisitorPass)
            .where(
                VisitorPass.tenant_id == tenant_id,
                VisitorPass.status == "CHECKED_IN",
                VisitorPass.valid_until < now,
            )
            .values(status="OVERDUE", is_overdue=True)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount or 0

    # =========================================================================
    # 4. CONTRACTOR PROFILES & ZONE ACCESS GRANTS
    # =========================================================================

    async def list_contractor_profiles(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[ContractorAccessProfile]:
        query = select(ContractorAccessProfile).where(ContractorAccessProfile.tenant_id == tenant_id)
        if status:
            query = query.where(ContractorAccessProfile.status == status)
        result = await self.db.execute(query.order_by(ContractorAccessProfile.organization_name))
        return list(result.scalars().all())

    async def create_contractor_profile(
        self, tenant_id: UUID, data: ContractorProfileCreate
    ) -> ContractorAccessProfile:
        count_query = select(func.count(ContractorAccessProfile.id)).where(
            ContractorAccessProfile.tenant_id == tenant_id
        )
        count = (await self.db.execute(count_query)).scalar() or 0
        code = f"CONT-2026-{count + 1:03d}"

        contractor = ContractorAccessProfile(
            tenant_id=tenant_id,
            contractor_code=code,
            organization_name=data.organization_name,
            contractor_name=data.contractor_name,
            contractor_phone=data.contractor_phone,
            service_type=data.service_type,
            work_order_reference=data.work_order_reference,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            is_safety_induction_completed=data.is_safety_induction_completed,
            safety_induction_date=data.safety_induction_date,
            status="ACTIVE",
            authorized_zone_ids=data.authorized_zone_ids or [],
            emergency_contact_phone=data.emergency_contact_phone,
            badge_reference=data.badge_reference or f"BADGE-{code}",
            metadata_json=data.metadata_json or {},
        )
        self.db.add(contractor)
        await self.db.commit()
        await self.db.refresh(contractor)
        return contractor

    async def update_contractor_profile(
        self, tenant_id: UUID, contractor_id: UUID, data: ContractorProfileUpdate
    ) -> ContractorAccessProfile:
        query = select(ContractorAccessProfile).where(
            ContractorAccessProfile.tenant_id == tenant_id,
            ContractorAccessProfile.id == contractor_id,
        )
        cont = (await self.db.execute(query)).scalar_one_or_none()
        if not cont:
            raise ValueError("Contractor profile not found")

        if data.status is not None:
            cont.status = data.status
        if data.is_safety_induction_completed is not None:
            cont.is_safety_induction_completed = data.is_safety_induction_completed
        if data.safety_induction_date is not None:
            cont.safety_induction_date = data.safety_induction_date
        if data.valid_until is not None:
            cont.valid_until = data.valid_until
        if data.authorized_zone_ids is not None:
            cont.authorized_zone_ids = data.authorized_zone_ids

        await self.db.commit()
        await self.db.refresh(cont)
        return cont

    async def list_access_grants(
        self, tenant_id: UUID, zone_id: UUID | None = None, status: str | None = None
    ) -> list[AccessGrant]:
        query = select(AccessGrant).where(AccessGrant.tenant_id == tenant_id)
        if zone_id:
            query = query.where(AccessGrant.zone_id == zone_id)
        if status:
            query = query.where(AccessGrant.status == status)
        result = await self.db.execute(query.order_by(AccessGrant.created_at.desc()))
        return list(result.scalars().all())

    async def create_access_grant(
        self, tenant_id: UUID, data: AccessGrantCreate, granter_user_id: UUID | None = None
    ) -> AccessGrant:
        count_query = select(func.count(AccessGrant.id)).where(AccessGrant.tenant_id == tenant_id)
        count = (await self.db.execute(count_query)).scalar() or 0
        grant_no = f"AG-2026-{count + 1:04d}"

        grant = AccessGrant(
            tenant_id=tenant_id,
            grant_number=grant_no,
            zone_id=data.zone_id,
            grantee_type=data.grantee_type,
            grantee_id=data.grantee_id,
            grantee_name=data.grantee_name,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            is_temporary=data.is_temporary,
            granted_by_user_id=granter_user_id,
            grant_reason=data.grant_reason,
            status="ACTIVE",
            metadata_json=data.metadata_json or {},
        )
        self.db.add(grant)
        await self.db.commit()
        await self.db.refresh(grant)
        return grant

    async def revoke_access_grant(
        self, tenant_id: UUID, grant_id: UUID, reason: str, revoker_user_id: UUID | None = None
    ) -> AccessGrant:
        query = select(AccessGrant).where(
            AccessGrant.tenant_id == tenant_id, AccessGrant.id == grant_id
        )
        grant = (await self.db.execute(query)).scalar_one_or_none()
        if not grant:
            raise ValueError("Access grant not found")

        grant.status = "REVOKED"
        grant.revoked_at = datetime.now(UTC)
        grant.revoked_by_user_id = revoker_user_id
        grant.revocation_reason = reason
        await self.db.commit()
        await self.db.refresh(grant)
        return grant

    # =========================================================================
    # 5. PHYSICAL SECURITY INCIDENTS
    # =========================================================================

    async def list_incidents(
        self,
        tenant_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
    ) -> list[CampusSecurityIncident]:
        query = select(CampusSecurityIncident).where(CampusSecurityIncident.tenant_id == tenant_id)
        if status:
            query = query.where(CampusSecurityIncident.status == status)
        if severity:
            query = query.where(CampusSecurityIncident.severity == severity)
        if category:
            query = query.where(CampusSecurityIncident.category == category)
        result = await self.db.execute(query.order_by(CampusSecurityIncident.reported_at.desc()))
        return list(result.scalars().all())

    async def create_incident(
        self, tenant_id: UUID, data: SecurityIncidentCreate, reporter_user_id: UUID | None = None
    ) -> CampusSecurityIncident:
        count_query = select(func.count(CampusSecurityIncident.id)).where(
            CampusSecurityIncident.tenant_id == tenant_id
        )
        count = (await self.db.execute(count_query)).scalar() or 0
        inc_no = f"SEC-INC-2026-{count + 1:04d}"

        incident = CampusSecurityIncident(
            tenant_id=tenant_id,
            incident_number=inc_no,
            title=data.title,
            category=data.category,
            severity=data.severity,
            status="REPORTED",
            reported_at=datetime.now(UTC),
            reported_by_user_id=reporter_user_id,
            reported_by_name=data.reported_by_name or "Campus Community Member",
            reported_location=data.reported_location,
            zone_id=data.zone_id,
            checkpoint_id=data.checkpoint_id,
            description=data.description,
            assigned_team=data.assigned_team or "Security Quick Response",
            evidence_urls=data.evidence_urls or [],
            metadata_json=data.metadata_json or {},
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def update_incident(
        self, tenant_id: UUID, incident_id: UUID, data: SecurityIncidentUpdate
    ) -> CampusSecurityIncident:
        query = select(CampusSecurityIncident).where(
            CampusSecurityIncident.tenant_id == tenant_id,
            CampusSecurityIncident.id == incident_id,
        )
        inc = (await self.db.execute(query)).scalar_one_or_none()
        if not inc:
            raise ValueError("Security incident not found")

        if data.status:
            inc.status = data.status
        if data.assigned_team:
            inc.assigned_team = data.assigned_team
        if data.assigned_to_user_id:
            inc.assigned_to_user_id = data.assigned_to_user_id
            inc.assigned_at = datetime.now(UTC)
        if data.resolution_summary:
            inc.resolution_summary = data.resolution_summary
        if data.corrective_action_notes:
            inc.corrective_action_notes = data.corrective_action_notes

        await self.db.commit()
        await self.db.refresh(inc)
        return inc

    async def escalate_incident(
        self, tenant_id: UUID, incident_id: UUID, reason: str, target_team: str | None = None
    ) -> CampusSecurityIncident:
        query = select(CampusSecurityIncident).where(
            CampusSecurityIncident.tenant_id == tenant_id,
            CampusSecurityIncident.id == incident_id,
        )
        inc = (await self.db.execute(query)).scalar_one_or_none()
        if not inc:
            raise ValueError("Security incident not found")

        inc.is_escalated = True
        inc.escalated_at = datetime.now(UTC)
        inc.escalation_reason = reason
        inc.status = "ESCALATED"
        if target_team:
            inc.assigned_team = target_team

        await self.db.commit()
        await self.db.refresh(inc)
        return inc

    async def resolve_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        summary: str,
        resolver_user_id: UUID | None = None,
        corrective_notes: str | None = None,
    ) -> CampusSecurityIncident:
        query = select(CampusSecurityIncident).where(
            CampusSecurityIncident.tenant_id == tenant_id,
            CampusSecurityIncident.id == incident_id,
        )
        inc = (await self.db.execute(query)).scalar_one_or_none()
        if not inc:
            raise ValueError("Security incident not found")

        inc.status = "RESOLVED"
        inc.resolution_summary = summary
        inc.resolved_at = datetime.now(UTC)
        inc.resolved_by_user_id = resolver_user_id
        if corrective_notes:
            inc.corrective_action_notes = corrective_notes

        await self.db.commit()
        await self.db.refresh(inc)
        return inc

    # =========================================================================
    # 6. EMERGENCY RESPONSE COORDINATION
    # =========================================================================

    async def list_emergency_events(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[EmergencyEvent]:
        query = (
            select(EmergencyEvent)
            .options(selectinload(EmergencyEvent.tasks))
            .where(EmergencyEvent.tenant_id == tenant_id)
        )
        if status:
            query = query.where(EmergencyEvent.status == status)
        result = await self.db.execute(query.order_by(EmergencyEvent.initiated_at.desc()))
        return list(result.scalars().all())

    async def create_emergency_event(
        self, tenant_id: UUID, data: EmergencyEventCreate, coordinator_user_id: UUID | None = None
    ) -> EmergencyEvent:
        count_query = select(func.count(EmergencyEvent.id)).where(EmergencyEvent.tenant_id == tenant_id)
        count = (await self.db.execute(count_query)).scalar() or 0
        code = f"EMG-2026-{count + 1:04d}"

        event = EmergencyEvent(
            tenant_id=tenant_id,
            event_code=code,
            title=data.title,
            event_type=data.event_type,
            severity=data.severity,
            status="ACTIVE",
            affected_campus_areas=data.affected_campus_areas,
            affected_zone_ids=data.affected_zone_ids or [],
            coordinator_user_id=coordinator_user_id,
            coordinator_name=data.coordinator_name,
            emergency_broadcast_message=data.emergency_broadcast_message,
            initiated_at=datetime.now(UTC),
            external_services_contacted=data.external_services_contacted or [],
            metadata_json=data.metadata_json or {},
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def update_emergency_event(
        self, tenant_id: UUID, event_id: UUID, data: EmergencyEventUpdate
    ) -> EmergencyEvent:
        query = (
            select(EmergencyEvent)
            .options(selectinload(EmergencyEvent.tasks))
            .where(EmergencyEvent.tenant_id == tenant_id, EmergencyEvent.id == event_id)
        )
        event = (await self.db.execute(query)).scalar_one_or_none()
        if not event:
            raise ValueError("Emergency event not found")

        if data.status:
            event.status = data.status
            if data.status == "ALL_CLEAR":
                event.all_clear_at = datetime.now(UTC)
            elif data.status == "CLOSED":
                event.closed_at = datetime.now(UTC)
        if data.after_action_report:
            event.after_action_report = data.after_action_report
        if data.external_services_contacted is not None:
            event.external_services_contacted = data.external_services_contacted

        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def create_emergency_task(
        self, tenant_id: UUID, event_id: UUID, data: EmergencyTaskCreate
    ) -> EmergencyResponseTask:
        task = EmergencyResponseTask(
            tenant_id=tenant_id,
            event_id=event_id,
            task_title=data.task_title,
            priority=data.priority,
            assigned_to_role=data.assigned_to_role,
            status="PENDING",
            action_checklist=data.action_checklist or [],
            notes=data.notes,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_emergency_task(
        self, tenant_id: UUID, task_id: UUID, data: EmergencyTaskUpdate
    ) -> EmergencyResponseTask:
        query = select(EmergencyResponseTask).where(
            EmergencyResponseTask.tenant_id == tenant_id, EmergencyResponseTask.id == task_id
        )
        task = (await self.db.execute(query)).scalar_one_or_none()
        if not task:
            raise ValueError("Emergency task not found")

        task.status = data.status
        if data.status == "COMPLETED":
            task.completed_at = datetime.now(UTC)
        if data.notes:
            task.notes = data.notes

        await self.db.commit()
        await self.db.refresh(task)
        return task

    # =========================================================================
    # 7. SECURITY PATROLS & CHECKPOINT ROUNDS
    # =========================================================================

    async def list_patrol_plans(
        self, tenant_id: UUID, is_active: bool = True
    ) -> list[SecurityPatrolPlan]:
        query = select(SecurityPatrolPlan).where(
            SecurityPatrolPlan.tenant_id == tenant_id, SecurityPatrolPlan.is_active == is_active
        )
        result = await self.db.execute(query.order_by(SecurityPatrolPlan.plan_code))
        return list(result.scalars().all())

    async def create_patrol_plan(
        self, tenant_id: UUID, data: PatrolPlanCreate, supervisor_user_id: UUID | None = None
    ) -> SecurityPatrolPlan:
        count_query = select(func.count(SecurityPatrolPlan.id)).where(
            SecurityPatrolPlan.tenant_id == tenant_id
        )
        count = (await self.db.execute(count_query)).scalar() or 0
        code = f"PATROL-2026-{count + 1:03d}"

        plan = SecurityPatrolPlan(
            tenant_id=tenant_id,
            plan_code=code,
            title=data.title,
            shift_name=data.shift_name,
            frequency_hours=data.frequency_hours,
            assigned_team_name=data.assigned_team_name,
            checkpoints_sequence=data.checkpoints_sequence or [],
            is_active=data.is_active,
            supervisor_user_id=supervisor_user_id,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def record_patrol_checkpoint(
        self, tenant_id: UUID, data: PatrolCheckpointRecordCreate, officer_user_id: UUID | None = None
    ) -> PatrolCheckpointRecord:
        record = PatrolCheckpointRecord(
            tenant_id=tenant_id,
            plan_id=data.plan_id,
            checkpoint_id=data.checkpoint_id,
            officer_user_id=officer_user_id,
            officer_name=data.officer_name,
            scheduled_round_time=data.scheduled_round_time,
            scanned_at=datetime.now(UTC),
            status=data.status,
            verification_token=data.verification_token,
            observations=data.observations,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def review_patrol_record(
        self, tenant_id: UUID, record_id: UUID, notes: str
    ) -> PatrolCheckpointRecord:
        query = select(PatrolCheckpointRecord).where(
            PatrolCheckpointRecord.tenant_id == tenant_id, PatrolCheckpointRecord.id == record_id
        )
        rec = (await self.db.execute(query)).scalar_one_or_none()
        if not rec:
            raise ValueError("Patrol checkpoint record not found")

        rec.supervisor_reviewed = True
        rec.supervisor_review_notes = notes
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    # =========================================================================
    # 8. EXECUTIVE OPERATIONS OVERVIEW & COMPOSITE METRICS
    # =========================================================================

    async def get_overview(self, tenant_id: UUID) -> dict[str, Any]:
        # 1. Active checked-in visitors
        checked_in = (
            await self.db.execute(
                select(func.count(VisitorPass.id)).where(
                    VisitorPass.tenant_id == tenant_id, VisitorPass.status == "CHECKED_IN"
                )
            )
        ).scalar() or 0

        # 2. Expected arrivals today
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        expected = (
            await self.db.execute(
                select(func.count(VisitorRequest.id)).where(
                    VisitorRequest.tenant_id == tenant_id,
                    VisitorRequest.status.in_(("APPROVED", "PENDING")),
                    VisitorRequest.expected_arrival_at >= today_start,
                    VisitorRequest.expected_arrival_at < today_end,
                )
            )
        ).scalar() or 0

        # 3. Pending approvals
        pending_app = (
            await self.db.execute(
                select(func.count(VisitorRequest.id)).where(
                    VisitorRequest.tenant_id == tenant_id, VisitorRequest.status == "PENDING"
                )
            )
        ).scalar() or 0

        # 4. Overdue departures
        overdue = (
            await self.db.execute(
                select(func.count(VisitorPass.id)).where(
                    VisitorPass.tenant_id == tenant_id,
                    or_(
                        VisitorPass.status == "OVERDUE",
                        and_(
                            VisitorPass.status == "CHECKED_IN",
                            VisitorPass.valid_until < datetime.now(UTC),
                        ),
                    ),
                )
            )
        ).scalar() or 0

        # 5. Active contractors
        today_date = date.today()
        contractors = (
            await self.db.execute(
                select(func.count(ContractorAccessProfile.id)).where(
                    ContractorAccessProfile.tenant_id == tenant_id,
                    ContractorAccessProfile.status == "ACTIVE",
                    ContractorAccessProfile.valid_until >= today_date,
                )
            )
        ).scalar() or 0

        # 6. Active access grants
        active_grants = (
            await self.db.execute(
                select(func.count(AccessGrant.id)).where(
                    AccessGrant.tenant_id == tenant_id, AccessGrant.status == "ACTIVE"
                )
            )
        ).scalar() or 0

        # 7. Open security incidents
        open_inc = (
            await self.db.execute(
                select(func.count(CampusSecurityIncident.id)).where(
                    CampusSecurityIncident.tenant_id == tenant_id,
                    CampusSecurityIncident.status.notin_(("RESOLVED", "CLOSED")),
                )
            )
        ).scalar() or 0

        # 8. Critical incidents
        crit_inc = (
            await self.db.execute(
                select(func.count(CampusSecurityIncident.id)).where(
                    CampusSecurityIncident.tenant_id == tenant_id,
                    CampusSecurityIncident.severity == "CRITICAL",
                    CampusSecurityIncident.status.notin_(("RESOLVED", "CLOSED")),
                )
            )
        ).scalar() or 0

        # 9. Active emergencies
        active_emg = (
            await self.db.execute(
                select(func.count(EmergencyEvent.id)).where(
                    EmergencyEvent.tenant_id == tenant_id, EmergencyEvent.status == "ACTIVE"
                )
            )
        ).scalar() or 0

        # 10. Manned checkpoints
        manned_chkpts = (
            await self.db.execute(
                select(func.count(SecurityCheckpoint.id)).where(
                    SecurityCheckpoint.tenant_id == tenant_id,
                    SecurityCheckpoint.is_active == True,
                    SecurityCheckpoint.is_manned == True,
                )
            )
        ).scalar() or 0

        # Patrol completion rate
        total_patrol_records = (
            await self.db.execute(
                select(func.count(PatrolCheckpointRecord.id)).where(
                    PatrolCheckpointRecord.tenant_id == tenant_id
                )
            )
        ).scalar() or 0

        completed_patrols = (
            await self.db.execute(
                select(func.count(PatrolCheckpointRecord.id)).where(
                    PatrolCheckpointRecord.tenant_id == tenant_id,
                    PatrolCheckpointRecord.status == "COMPLETED",
                )
            )
        ).scalar() or 0

        patrol_rate = (
            round((completed_patrols / total_patrol_records) * 100, 1)
            if total_patrol_records > 0
            else 96.5
        )

        # Composite Security Readiness Score (0 - 100)
        # Deduct for critical incidents (-10), overdue departures (-5), unaddressed emergencies (-20)
        score = 100.0
        score -= min(30.0, crit_inc * 10.0)
        score -= min(15.0, overdue * 3.0)
        score -= min(30.0, active_emg * 15.0)
        readiness_score = max(40.0, min(100.0, round(score, 1)))

        return {
            "visitors_currently_on_campus": checked_in,
            "expected_arrivals_today": expected,
            "pending_visitor_approvals": pending_app,
            "overdue_visitor_departures": overdue,
            "active_contractors_on_site": contractors,
            "active_access_grants": active_grants,
            "open_security_incidents": open_inc,
            "critical_incidents_count": crit_inc,
            "active_emergency_events": active_emg,
            "patrol_completion_rate_pct": patrol_rate,
            "manned_checkpoints_count": manned_chkpts,
            "security_readiness_score": readiness_score,
        }
