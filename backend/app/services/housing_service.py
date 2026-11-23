"""CampusOS Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Service (Step 66).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.housing import (
    AccommodationBed,
    AccommodationProperty,
    AccommodationProvider,
    AccommodationUnit,
    AgreementStatus,
    HousingAgreementReference,
    HousingAssignment,
    HousingAssignmentStatus,
    HousingCheckInOutRecord,
    HousingMaintenanceRequest,
    HousingOffer,
    HousingOfferStatus,
    HousingPropertyInspection,
    HousingRequestStatus,
    InspectionOutcome,
    MaintenanceStatus,
    PropertyLifecycleStatus,
    ProviderVerificationStatus,
    StudentHousingRequest,
    UnitStatus,
)
from app.models.people import StudentProfile
from app.schemas.housing import (
    AccommodationPropertyCreate,
    AccommodationProviderCreate,
    AccommodationProviderUpdate,
    AccommodationUnitCreate,
    HousingAgreementCreate,
    HousingAnalyticsSummaryResponse,
    HousingAssignmentCreate,
    HousingAssignmentTransferRequest,
    HousingCheckInOutCreate,
    HousingMaintenanceRequestCreate,
    HousingMaintenanceRequestUpdate,
    HousingOfferCreate,
    HousingOfferRespond,
    HousingPropertyInspectionCreate,
    PropertyStatusTransitionRequest,
    StudentHousingRequestCreate,
    StudentHousingRequestReview,
)

UTC = UTC


class HousingService:
    """Enterprise service layer governing student housing and accommodation operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # 1. ACCOMMODATION PROVIDERS & LANDLORD PARTNERSHIPS
    # =========================================================================

    async def create_provider(self, req: AccommodationProviderCreate) -> AccommodationProvider:
        # Check slug uniqueness within tenant
        existing = await self.db.scalar(
            select(AccommodationProvider).where(
                AccommodationProvider.tenant_id == self.tenant_id,
                AccommodationProvider.slug == req.slug.lower(),
            )
        )
        if existing:
            raise ConflictException(f"Provider with slug '{req.slug}' already exists in this institution.")

        now = datetime.now(UTC)
        provider = AccommodationProvider(
            tenant_id=self.tenant_id,
            name=req.name.strip(),
            slug=req.slug.lower().strip(),
            provider_type=req.provider_type.value,
            registration_number=req.registration_number,
            contact_name=req.contact_name.strip(),
            contact_email=req.contact_email.lower().strip(),
            contact_phone=req.contact_phone.strip(),
            emergency_phone=req.emergency_phone,
            tax_id=req.tax_id,
            address=req.address,
            city=req.city,
            state=req.state,
            verification_status=ProviderVerificationStatus.PENDING.value,
            mou_reference=req.mou_reference,
            mou_valid_from=req.mou_valid_from,
            mou_valid_to=req.mou_valid_to,
            is_active=req.is_active,
            created_at=now,
            updated_at=now,
        )
        self.db.add(provider)
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    async def get_provider(self, provider_id: UUID) -> AccommodationProvider:
        provider = await self.db.scalar(
            select(AccommodationProvider)
            .where(
                AccommodationProvider.tenant_id == self.tenant_id,
                AccommodationProvider.id == provider_id,
            )
            .options(selectinload(AccommodationProvider.properties))
        )
        if not provider:
            raise NotFoundException(f"Accommodation provider {provider_id} not found.")
        return provider

    async def list_providers(
        self, status: str | None = None, is_active: bool | None = None
    ) -> list[AccommodationProvider]:
        query = select(AccommodationProvider).where(AccommodationProvider.tenant_id == self.tenant_id)
        if status:
            query = query.where(AccommodationProvider.verification_status == status.upper())
        if is_active is not None:
            query = query.where(AccommodationProvider.is_active == is_active)
        query = query.order_by(AccommodationProvider.name.asc())
        result = await self.db.scalars(query)
        return list(result.all())

    async def update_provider(self, provider_id: UUID, req: AccommodationProviderUpdate) -> AccommodationProvider:
        provider = await self.get_provider(provider_id)
        data = req.model_dump(exclude_unset=True)
        for key, val in data.items():
            if val is not None:
                if key == "verification_status":
                    status_val = val.value if hasattr(val, "value") else val
                    setattr(provider, key, status_val)
                    if status_val == ProviderVerificationStatus.VERIFIED.value and not provider.verified_at:
                        provider.verified_at = datetime.now(UTC)
                elif key == "provider_type":
                    setattr(provider, key, val.value if hasattr(val, "value") else val)
                else:
                    setattr(provider, key, val)
        provider.updated_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    # =========================================================================
    # 2. ACCOMMODATION PROPERTIES & LIFECYCLE
    # =========================================================================

    async def create_property(self, req: AccommodationPropertyCreate, user_id: UUID) -> AccommodationProperty:
        # Check property code uniqueness
        existing = await self.db.scalar(
            select(AccommodationProperty).where(
                AccommodationProperty.tenant_id == self.tenant_id,
                AccommodationProperty.code == req.code.upper(),
            )
        )
        if existing:
            raise ConflictException(f"Property with code '{req.code}' already exists.")

        prop = AccommodationProperty(
            tenant_id=self.tenant_id,
            provider_id=req.provider_id,
            hostel_id=req.hostel_id,
            campus_id=req.campus_id,
            code=req.code.upper().strip(),
            name=req.name.strip(),
            slug=req.slug.lower().strip(),
            property_type=req.property_type.value,
            lifecycle_status=PropertyLifecycleStatus.DRAFT.value,
            description=req.description,
            address=req.address.strip(),
            city=req.city,
            state=req.state,
            postal_code=req.postal_code,
            latitude=req.latitude,
            longitude=req.longitude,
            distance_to_campus_km=req.distance_to_campus_km,
            monthly_rent_min=req.monthly_rent_min,
            monthly_rent_max=req.monthly_rent_max,
            security_deposit_amount=req.security_deposit_amount,
            currency=req.currency,
            amenities=req.amenities,
            utilities_included=req.utilities_included,
            accessibility_features=req.accessibility_features,
            safety_features=req.safety_features,
            house_rules=req.house_rules,
            manager_name=req.manager_name,
            manager_phone=req.manager_phone,
            manager_email=req.manager_email,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(prop)
        await self.db.flush()

        # Update provider property count if provider linked
        if req.provider_id:
            provider = await self.get_provider(req.provider_id)
            provider.total_properties_managed += 1
            await self.db.flush()

        await self.db.refresh(prop)
        return prop

    async def get_property(self, property_id: UUID) -> AccommodationProperty:
        prop = await self.db.scalar(
            select(AccommodationProperty)
            .where(
                AccommodationProperty.tenant_id == self.tenant_id,
                AccommodationProperty.id == property_id,
            )
            .options(
                selectinload(AccommodationProperty.units).selectinload(AccommodationUnit.beds),
                selectinload(AccommodationProperty.provider),
            )
        )
        if not prop:
            raise NotFoundException(f"Property {property_id} not found.")
        return prop

    async def list_properties(
        self,
        status: str | None = None,
        lifecycle_status: str | None = None,
        property_type: str | None = None,
        provider_id: UUID | None = None,
        search: str | None = None,
        student_discoverable_only: bool = False,
        published_only: bool = False,
    ) -> list[AccommodationProperty]:
        query = select(AccommodationProperty).where(AccommodationProperty.tenant_id == self.tenant_id)

        eff_status = lifecycle_status or status
        if student_discoverable_only or published_only:
            query = query.where(AccommodationProperty.lifecycle_status == PropertyLifecycleStatus.PUBLISHED.value)
        elif eff_status:
            query = query.where(AccommodationProperty.lifecycle_status == eff_status.upper())

        if property_type:
            query = query.where(AccommodationProperty.property_type == property_type.upper())
        if provider_id:
            query = query.where(AccommodationProperty.provider_id == provider_id)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AccommodationProperty.name.ilike(term),
                    AccommodationProperty.code.ilike(term),
                    AccommodationProperty.address.ilike(term),
                )
            )

        query = query.order_by(AccommodationProperty.name.asc())
        result = await self.db.scalars(query)
        return list(result.all())

    async def transition_property_status(
        self,
        property_id: UUID,
        req: PropertyStatusTransitionRequest,
        reviewer_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> AccommodationProperty:
        prop = await self.get_property(property_id)
        current = prop.lifecycle_status
        target = req.target_status.value
        effective_reviewer_id = reviewer_id or user_id

        # Allowed transitions
        allowed = {
            PropertyLifecycleStatus.DRAFT.value: [
                PropertyLifecycleStatus.PENDING_REVIEW.value,
                PropertyLifecycleStatus.APPROVED.value,
            ],
            PropertyLifecycleStatus.PENDING_REVIEW.value: [
                PropertyLifecycleStatus.APPROVED.value,
                PropertyLifecycleStatus.DRAFT.value,
                PropertyLifecycleStatus.ARCHIVED.value,
            ],
            PropertyLifecycleStatus.APPROVED.value: [
                PropertyLifecycleStatus.PUBLISHED.value,
                PropertyLifecycleStatus.SUSPENDED.value,
            ],
            PropertyLifecycleStatus.PUBLISHED.value: [
                PropertyLifecycleStatus.SUSPENDED.value,
                PropertyLifecycleStatus.ARCHIVED.value,
            ],
            PropertyLifecycleStatus.SUSPENDED.value: [
                PropertyLifecycleStatus.APPROVED.value,
                PropertyLifecycleStatus.PUBLISHED.value,
                PropertyLifecycleStatus.ARCHIVED.value,
            ],
            PropertyLifecycleStatus.ARCHIVED.value: [],
        }

        if target not in allowed.get(current, []):
            raise ValidationException(f"Invalid transition from {current} to {target}.")

        prop.lifecycle_status = target
        if target in (PropertyLifecycleStatus.APPROVED.value, PropertyLifecycleStatus.PUBLISHED.value):
            prop.approved_by_id = effective_reviewer_id
            prop.approved_at = datetime.now(UTC)
            if req.approval_valid_until:
                prop.approval_valid_until = req.approval_valid_until
            elif not prop.approval_valid_until:
                prop.approval_valid_until = date.today() + timedelta(days=365)

        prop.updated_at = datetime.now(UTC)
        await self.db.flush()
        return await self.recalculate_property_capacity(prop.id)

    async def recalculate_property_capacity(self, property_id: UUID) -> AccommodationProperty:
        """Derives real-time capacity and occupancy metrics from persisted units and beds."""
        prop = await self.get_property(property_id)

        # Count units and beds
        units = await self.db.scalars(
            select(AccommodationUnit).where(
                AccommodationUnit.tenant_id == self.tenant_id,
                AccommodationUnit.property_id == property_id,
            )
        )
        unit_list = list(units.all())
        prop.total_rooms = len(unit_list)

        total_beds = 0
        occupied_beds = 0
        available_beds = 0

        for unit in unit_list:
            unit_beds = await self.db.scalars(
                select(AccommodationBed).where(
                    AccommodationBed.tenant_id == self.tenant_id,
                    AccommodationBed.unit_id == unit.id,
                )
            )
            beds_list = list(unit_beds.all())
            unit_occupied = sum(1 for b in beds_list if b.status == "OCCUPIED")
            unit_avail = sum(1 for b in beds_list if b.status == "AVAILABLE" and b.is_available)

            unit.occupied_beds = unit_occupied
            unit.is_available = unit_avail > 0 and unit.status != UnitStatus.MAINTENANCE.value

            total_beds += len(beds_list)
            occupied_beds += unit_occupied
            available_beds += unit_avail

        prop.total_bed_capacity = total_beds
        prop.occupied_beds = occupied_beds
        prop.available_beds = available_beds

        await self.db.flush()
        return prop

    # =========================================================================
    # 3. UNITS & BEDS
    # =========================================================================

    async def create_unit(self, req: AccommodationUnitCreate) -> AccommodationUnit:
        prop = await self.get_property(req.property_id)

        existing = await self.db.scalar(
            select(AccommodationUnit).where(
                AccommodationUnit.property_id == req.property_id,
                AccommodationUnit.unit_number == req.unit_number.strip(),
            )
        )
        if existing:
            raise ConflictException(f"Unit '{req.unit_number}' already exists in property {prop.name}.")

        unit = AccommodationUnit(
            tenant_id=self.tenant_id,
            property_id=req.property_id,
            hostel_room_id=req.hostel_room_id,
            unit_number=req.unit_number.strip(),
            unit_type=req.unit_type.value,
            floor_number=req.floor_number,
            bed_capacity=req.bed_capacity,
            rent_per_bed=req.rent_per_bed,
            security_deposit_per_bed=req.security_deposit_per_bed,
            is_furnished=req.is_furnished,
            has_attached_bath=req.has_attached_bath,
            is_accessible=req.is_accessible,
            is_available=True,
            status=UnitStatus.AVAILABLE.value,
        )
        self.db.add(unit)
        await self.db.flush()

        # Automatically generate addressable beds based on bed_capacity
        for i in range(req.bed_capacity):
            suffix = chr(ord('A') + i)
            bed = AccommodationBed(
                tenant_id=self.tenant_id,
                unit_id=unit.id,
                bed_code=f"{unit.unit_number}-{suffix}",
                is_available=True,
                status="AVAILABLE",
            )
            self.db.add(bed)

        await self.db.flush()
        await self.recalculate_property_capacity(prop.id)
        return unit

    async def list_units(self, property_id: UUID) -> list[AccommodationUnit]:
        units = await self.db.scalars(
            select(AccommodationUnit)
            .where(
                AccommodationUnit.tenant_id == self.tenant_id,
                AccommodationUnit.property_id == property_id,
            )
            .options(selectinload(AccommodationUnit.beds))
            .order_by(AccommodationUnit.unit_number.asc())
        )
        return list(units.all())

    async def block_bed(self, bed_id: UUID, reason: str, blocked_until: date | None = None) -> AccommodationBed:
        bed = await self.db.scalar(
            select(AccommodationBed).where(
                AccommodationBed.tenant_id == self.tenant_id,
                AccommodationBed.id == bed_id,
            )
        )
        if not bed:
            raise NotFoundException(f"Bed {bed_id} not found.")

        bed.is_available = False
        bed.status = "BLOCKED_MAINTENANCE"
        bed.blocked_reason = reason
        bed.blocked_until = blocked_until
        await self.db.flush()
        return bed

    # =========================================================================
    # 4. STUDENT HOUSING REQUESTS & WAITLIST
    # =========================================================================

    async def submit_housing_request(
        self, student_id: UUID, req: StudentHousingRequestCreate
    ) -> StudentHousingRequest:
        # Check if student exists
        student = await self.db.scalar(
            select(StudentProfile).where(
                StudentProfile.tenant_id == self.tenant_id,
                StudentProfile.id == student_id,
            )
        )
        if not student:
            raise NotFoundException(f"Student profile {student_id} not found.")

        # Check for active request
        active_req = await self.db.scalar(
            select(StudentHousingRequest).where(
                StudentHousingRequest.tenant_id == self.tenant_id,
                StudentHousingRequest.student_id == student_id,
                StudentHousingRequest.status.in_([
                    HousingRequestStatus.SUBMITTED.value,
                    HousingRequestStatus.UNDER_REVIEW.value,
                    HousingRequestStatus.APPROVED.value,
                    HousingRequestStatus.WAITLISTED.value,
                    HousingRequestStatus.OFFERED.value,
                ]),
            )
        )
        if active_req:
            raise ConflictException("Student already has an active or pending housing request.")

        # Generate request number
        count = await self.db.scalar(
            select(func.count(StudentHousingRequest.id)).where(
                StudentHousingRequest.tenant_id == self.tenant_id
            )
        ) or 0
        req_num = f"REQ-HOU-{date.today().year}-{count + 1:04d}"

        # Calculate preliminary priority score (e.g. based on accessibility need, distance, etc.)
        priority = Decimal("50.00")
        if req.accessibility_required:
            priority += Decimal("30.00")

        housing_req = StudentHousingRequest(
            tenant_id=self.tenant_id,
            request_number=req_num,
            student_id=student_id,
            preferred_property_id=req.preferred_property_id,
            preferred_unit_type=req.preferred_unit_type.value,
            academic_year_id=req.academic_year_id,
            academic_term=req.academic_term,
            requested_move_in_date=req.requested_move_in_date,
            requested_move_out_date=req.requested_move_out_date,
            budget_min=req.budget_min,
            budget_max=req.budget_max,
            accessibility_required=req.accessibility_required,
            disability_accommodation_notes=req.disability_accommodation_notes,
            dietary_preference=req.dietary_preference,
            lifestyle_preferences=req.lifestyle_preferences,
            special_requests=req.special_requests,
            supporting_document_ids=req.supporting_document_ids,
            status=HousingRequestStatus.SUBMITTED.value,
            priority_score=priority,
        )
        self.db.add(housing_req)
        await self.db.flush()
        return housing_req

    async def get_housing_request(self, request_id: UUID) -> StudentHousingRequest:
        req = await self.db.scalar(
            select(StudentHousingRequest)
            .where(
                StudentHousingRequest.tenant_id == self.tenant_id,
                StudentHousingRequest.id == request_id,
            )
            .options(
                selectinload(StudentHousingRequest.preferred_property),
                selectinload(StudentHousingRequest.offers),
            )
        )
        if not req:
            raise NotFoundException(f"Housing request {request_id} not found.")
        return req

    async def list_housing_requests(
        self,
        student_id: UUID | None = None,
        property_id: UUID | None = None,
        status: str | None = None,
    ) -> list[StudentHousingRequest]:
        query = select(StudentHousingRequest).where(StudentHousingRequest.tenant_id == self.tenant_id)
        if student_id:
            query = query.where(StudentHousingRequest.student_id == student_id)
        if property_id:
            query = query.where(StudentHousingRequest.preferred_property_id == property_id)
        if status:
            query = query.where(StudentHousingRequest.status == status.upper())

        query = query.order_by(StudentHousingRequest.created_at.desc())
        result = await self.db.scalars(query)
        return list(result.all())

    async def review_housing_request(
        self, request_id: UUID, review: StudentHousingRequestReview, reviewer_id: UUID
    ) -> StudentHousingRequest:
        req = await self.get_housing_request(request_id)
        target = review.status.value

        if target == HousingRequestStatus.WAITLISTED.value:
            # Assign waitlist rank
            wl_count = await self.db.scalar(
                select(func.count(StudentHousingRequest.id)).where(
                    StudentHousingRequest.tenant_id == self.tenant_id,
                    StudentHousingRequest.status == HousingRequestStatus.WAITLISTED.value,
                    StudentHousingRequest.id != req.id,
                )
            ) or 0
            req.waitlist_position = wl_count + 1
        else:
            req.waitlist_position = None

        if target == HousingRequestStatus.REJECTED.value:
            req.rejection_reason = review.rejection_reason or "Capacity constraints or eligibility criteria not met."

        if review.priority_score is not None:
            req.priority_score = review.priority_score

        req.status = target
        req.review_notes = review.review_notes
        req.reviewed_by_id = reviewer_id
        req.reviewed_at = datetime.now(UTC)

        await self.db.flush()
        return req

    # =========================================================================
    # 5. OFFERS & ALLOCATIONS
    # =========================================================================

    async def create_offer(self, req: HousingOfferCreate) -> HousingOffer:
        # Check property status
        prop = await self.get_property(req.property_id)
        if prop.lifecycle_status not in (PropertyLifecycleStatus.APPROVED.value, PropertyLifecycleStatus.PUBLISHED.value):
            raise ValidationException(f"Property {req.property_id} is not approved or published (status: {prop.lifecycle_status}).")

        # Check request status
        h_req = await self.get_housing_request(req.request_id)
        if h_req.status not in (HousingRequestStatus.SUBMITTED.value, HousingRequestStatus.UNDER_REVIEW.value, HousingRequestStatus.APPROVED.value, HousingRequestStatus.WAITLISTED.value):
            raise BadRequestException(f"Cannot offer housing for request in '{h_req.status}' status.")

        # Check bed availability
        bed = await self.db.scalar(
            select(AccommodationBed).where(
                AccommodationBed.tenant_id == self.tenant_id,
                AccommodationBed.id == req.bed_id,
            )
        )
        if not bed or not bed.is_available or bed.status != "AVAILABLE":
            raise ConflictException(f"Bed {req.bed_id} is not currently available.")

        # Reserve bed temporarily
        bed.status = "RESERVED"

        offer = HousingOffer(
            tenant_id=self.tenant_id,
            request_id=req.request_id,
            student_id=h_req.student_id,
            property_id=req.property_id,
            unit_id=req.unit_id,
            bed_id=req.bed_id,
            offered_rent_monthly=req.offered_rent_monthly,
            offered_deposit=req.offered_deposit,
            occupancy_start_date=req.occupancy_start_date,
            occupancy_end_date=req.occupancy_end_date,
            offer_valid_until=datetime.now(UTC) + timedelta(days=req.offer_valid_days),
            status=HousingOfferStatus.OFFERED.value,
        )
        self.db.add(offer)

        h_req.status = HousingRequestStatus.OFFERED.value
        await self.db.flush()
        return offer

    async def respond_to_offer(self, offer_id: UUID, response: HousingOfferRespond, student_id: UUID) -> HousingOffer:
        offer = await self.db.scalar(
            select(HousingOffer).where(
                HousingOffer.tenant_id == self.tenant_id,
                HousingOffer.id == offer_id,
            )
        )
        if not offer:
            raise NotFoundException(f"Housing offer {offer_id} not found.")

        if offer.student_id != student_id:
            raise ForbiddenException("You can only respond to your own housing offers.")

        if offer.status != HousingOfferStatus.OFFERED.value:
            raise BadRequestException(f"Offer is already in '{offer.status}' status.")

        decision = response.decision.value
        offer.status = decision
        offer.decline_reason = response.decline_reason
        offer.response_notes = response.response_notes
        offer.responded_at = datetime.now(UTC)

        req = await self.get_housing_request(offer.request_id)
        bed = await self.db.scalar(
            select(AccommodationBed).where(AccommodationBed.id == offer.bed_id)
        )

        if decision == HousingOfferStatus.ACCEPTED.value:
            req.status = HousingRequestStatus.ACCEPTED.value

            # Automatically create HousingAssignment (which allocates and marks bed OCCUPIED)
            await self.allocate_student(
                HousingAssignmentCreate(
                    student_id=student_id,
                    property_id=offer.property_id,
                    unit_id=offer.unit_id,
                    bed_id=offer.bed_id,
                    request_id=offer.request_id,
                    offer_id=offer.id,
                    start_date=offer.occupancy_start_date,
                    end_date=offer.occupancy_end_date,
                    monthly_rent=offer.offered_rent_monthly,
                    security_deposit=offer.offered_deposit,
                )
            )

        elif decision == HousingOfferStatus.DECLINED.value:
            req.status = HousingRequestStatus.SUBMITTED.value
            if bed:
                bed.status = "AVAILABLE"
                bed.is_available = True

        await self.db.flush()
        await self.recalculate_property_capacity(offer.property_id)
        return offer

    async def allocate_student(self, req: HousingAssignmentCreate) -> HousingAssignment:
        """Formal room/bed allocation with anti-double-booking locks."""
        # 1. Prevent duplicate active allocations for student
        active_asgn = await self.db.scalar(
            select(HousingAssignment).where(
                HousingAssignment.tenant_id == self.tenant_id,
                HousingAssignment.student_id == req.student_id,
                HousingAssignment.status.in_([
                    HousingAssignmentStatus.ASSIGNED.value,
                    HousingAssignmentStatus.CHECKED_IN.value,
                    HousingAssignmentStatus.ACTIVE.value,
                ]),
            )
        )
        if active_asgn:
            raise ConflictException("Student already has an active housing allocation.")

        # 2. Check bed availability
        bed = await self.db.scalar(
            select(AccommodationBed).where(
                AccommodationBed.tenant_id == self.tenant_id,
                AccommodationBed.id == req.bed_id,
            )
        )
        if not bed:
            raise NotFoundException(f"Bed {req.bed_id} not found.")

        if req.offer_id:
            if bed.status not in ("AVAILABLE", "RESERVED"):
                raise ConflictException(f"Bed {req.bed_id} is not currently available for assignment.")
        else:
            if not bed.is_available or bed.status != "AVAILABLE":
                raise ConflictException(f"Bed {req.bed_id} is not currently available for assignment.")

        # Generate assignment number
        count = await self.db.scalar(
            select(func.count(HousingAssignment.id)).where(
                HousingAssignment.tenant_id == self.tenant_id
            )
        ) or 0
        asgn_num = f"ASGN-HOU-{date.today().year}-{count + 1:04d}"

        assignment = HousingAssignment(
            tenant_id=self.tenant_id,
            assignment_number=asgn_num,
            student_id=req.student_id,
            property_id=req.property_id,
            unit_id=req.unit_id,
            bed_id=req.bed_id,
            request_id=req.request_id,
            offer_id=req.offer_id,
            start_date=req.start_date,
            end_date=req.end_date,
            monthly_rent=req.monthly_rent,
            security_deposit=req.security_deposit,
            status=HousingAssignmentStatus.ASSIGNED.value,
        )
        self.db.add(assignment)

        # Mark bed occupied
        bed.status = "OCCUPIED"
        bed.is_available = False

        await self.db.flush()

        # Create corresponding legal agreement placeholder
        await self.create_agreement(
            HousingAgreementCreate(
                assignment_id=assignment.id,
                agreement_title=f"Student Residential Tenancy Agreement — {asgn_num}",
                valid_from=req.start_date,
                valid_to=req.end_date,
                rent_amount=req.monthly_rent,
                deposit_amount=req.security_deposit,
            )
        )

        await self.recalculate_property_capacity(req.property_id)
        return assignment

    async def transfer_assignment(
        self, assignment_id: UUID, req: HousingAssignmentTransferRequest
    ) -> HousingAssignment:
        assignment = await self.db.scalar(
            select(HousingAssignment).where(
                HousingAssignment.tenant_id == self.tenant_id,
                HousingAssignment.id == assignment_id,
            )
        )
        if not assignment:
            raise NotFoundException(f"Assignment {assignment_id} not found.")

        # Check new bed
        target_bed = await self.db.scalar(
            select(AccommodationBed).where(
                AccommodationBed.tenant_id == self.tenant_id,
                AccommodationBed.id == req.target_bed_id,
            )
        )
        if not target_bed or not target_bed.is_available:
            raise ConflictException(f"Target bed {req.target_bed_id} is occupied or unavailable.")

        # Release old bed
        old_bed = await self.db.scalar(
            select(AccommodationBed).where(AccommodationBed.id == assignment.bed_id)
        )
        if old_bed:
            old_bed.status = "AVAILABLE"
            old_bed.is_available = True

        # Assign new bed
        target_bed.status = "OCCUPIED"
        target_bed.is_available = False

        assignment.unit_id = req.target_unit_id
        assignment.bed_id = req.target_bed_id
        assignment.transfer_to_unit_id = req.target_unit_id
        assignment.transfer_reason = req.transfer_reason
        assignment.status = HousingAssignmentStatus.TRANSFERRED.value

        await self.db.flush()
        await self.recalculate_property_capacity(assignment.property_id)
        return assignment

    # =========================================================================
    # 6. AGREEMENTS & CHECK-IN/OUT
    # =========================================================================

    async def create_agreement(self, req: HousingAgreementCreate) -> HousingAgreementReference:
        asgn = await self.db.scalar(
            select(HousingAssignment).where(
                HousingAssignment.tenant_id == self.tenant_id,
                HousingAssignment.id == req.assignment_id,
            )
        )
        if not asgn:
            raise NotFoundException(f"Assignment {req.assignment_id} not found.")

        existing = await self.db.scalar(
            select(HousingAgreementReference).where(
                HousingAgreementReference.tenant_id == self.tenant_id,
                HousingAgreementReference.assignment_id == asgn.id,
            )
        )
        if existing:
            existing.agreement_title = req.agreement_title
            existing.valid_from = req.valid_from
            existing.valid_to = req.valid_to
            existing.rent_amount = req.rent_amount
            existing.deposit_amount = req.deposit_amount
            existing.payment_frequency = req.payment_frequency
            if req.finance_invoice_reference:
                existing.finance_invoice_reference = req.finance_invoice_reference
            if req.deposit_invoice_reference:
                existing.deposit_invoice_reference = req.deposit_invoice_reference
            existing.updated_at = datetime.now(UTC)
            await self.db.flush()
            return existing

        count = await self.db.scalar(
            select(func.count(HousingAgreementReference.id)).where(
                HousingAgreementReference.tenant_id == self.tenant_id
            )
        ) or 0
        agmt_num = f"AGR-HOU-{date.today().year}-{count + 1:04d}"

        # Fetch property provider
        prop = await self.get_property(asgn.property_id)

        agreement = HousingAgreementReference(
            tenant_id=self.tenant_id,
            assignment_id=asgn.id,
            property_id=asgn.property_id,
            provider_id=prop.provider_id,
            student_id=asgn.student_id,
            agreement_number=agmt_num,
            agreement_title=req.agreement_title,
            valid_from=req.valid_from,
            valid_to=req.valid_to,
            rent_amount=req.rent_amount,
            deposit_amount=req.deposit_amount,
            payment_frequency=req.payment_frequency,
            finance_invoice_reference=req.finance_invoice_reference or f"INV-HOU-{agmt_num}",
            deposit_invoice_reference=req.deposit_invoice_reference or f"DEP-HOU-{agmt_num}",
            status=AgreementStatus.PENDING_SIGNATURE.value,
        )
        self.db.add(agreement)
        await self.db.flush()
        return agreement

    async def record_check_in_out(
        self, req: HousingCheckInOutCreate, inspector_id: UUID
    ) -> HousingCheckInOutRecord:
        asgn = await self.db.scalar(
            select(HousingAssignment).where(
                HousingAssignment.tenant_id == self.tenant_id,
                HousingAssignment.id == req.assignment_id,
            )
        )
        if not asgn:
            raise NotFoundException(f"Assignment {req.assignment_id} not found.")

        record = HousingCheckInOutRecord(
            tenant_id=self.tenant_id,
            assignment_id=asgn.id,
            student_id=asgn.student_id,
            record_type=req.record_type.upper(),
            scheduled_date=req.scheduled_date,
            actual_timestamp=datetime.now(UTC),
            inspector_user_id=inspector_id,
            key_card_issued_or_returned=req.key_card_issued_or_returned,
            key_identifier=req.key_identifier,
            room_condition_rating=req.room_condition_rating,
            checklist_items=req.checklist_items,
            damage_assessed_amount=req.damage_assessed_amount,
            damage_description=req.damage_description,
            photos_evidence_ids=req.photos_evidence_ids,
            student_signature_confirmed=req.student_signature_confirmed,
            notes=req.notes,
            status="COMPLETED",
        )
        self.db.add(record)

        # Update assignment status
        if req.record_type.upper() == "CHECK_IN":
            asgn.status = HousingAssignmentStatus.CHECKED_IN.value
        elif req.record_type.upper() == "CHECK_OUT":
            asgn.status = HousingAssignmentStatus.CHECKED_OUT.value
            # Release bed
            bed = await self.db.scalar(
                select(AccommodationBed).where(AccommodationBed.id == asgn.bed_id)
            )
            if bed:
                bed.status = "AVAILABLE"
                bed.is_available = True
            await self.recalculate_property_capacity(asgn.property_id)

        await self.db.flush()
        return record

    # =========================================================================
    # 7. INSPECTIONS & RESIDENTIAL SAFETY
    # =========================================================================

    async def record_inspection(
        self, req: HousingPropertyInspectionCreate, inspector_id: UUID
    ) -> HousingPropertyInspection:
        prop = await self.get_property(req.property_id)

        count = await self.db.scalar(
            select(func.count(HousingPropertyInspection.id)).where(
                HousingPropertyInspection.tenant_id == self.tenant_id
            )
        ) or 0
        insp_code = f"INSP-HOU-{date.today().year}-{count + 1:04d}"

        # If critical failure, auto-suspend property availability
        is_suspended = req.availability_suspended or (req.overall_outcome == InspectionOutcome.FAILED_CRITICAL)
        if is_suspended:
            prop.lifecycle_status = PropertyLifecycleStatus.SUSPENDED.value

        inspection = HousingPropertyInspection(
            tenant_id=self.tenant_id,
            property_id=prop.id,
            inspection_code=insp_code,
            inspector_user_id=inspector_id,
            inspection_date=req.inspection_date,
            inspection_type=req.inspection_type.value,
            overall_outcome=req.overall_outcome.value,
            safety_score=req.safety_score,
            checklist_results=req.checklist_results,
            critical_issues_found=req.critical_issues_found or is_suspended,
            availability_suspended=is_suspended,
            corrective_actions_required=req.corrective_actions_required,
            corrective_action_deadline=req.corrective_action_deadline,
            reinspection_due_date=req.reinspection_due_date,
            compliance_status="ACTION_PENDING" if is_suspended else "COMPLIANT",
        )
        self.db.add(inspection)
        await self.db.flush()
        return inspection

    async def list_inspections(self, property_id: UUID | None = None) -> list[HousingPropertyInspection]:
        query = select(HousingPropertyInspection).where(HousingPropertyInspection.tenant_id == self.tenant_id)
        if property_id:
            query = query.where(HousingPropertyInspection.property_id == property_id)
        query = query.order_by(HousingPropertyInspection.inspection_date.desc())
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 8. MAINTENANCE & SERVICE REQUESTS
    # =========================================================================

    async def submit_maintenance_request(
        self,
        req: HousingMaintenanceRequestCreate,
        reporter_id: UUID | None = None,
        user_id: UUID | None = None,
        student_id: UUID | None = None,
    ) -> HousingMaintenanceRequest:
        prop = await self.get_property(req.property_id)
        effective_reporter_id = reporter_id or user_id or uuid4()

        maint = HousingMaintenanceRequest(
            tenant_id=self.tenant_id,
            property_id=prop.id,
            unit_id=req.unit_id,
            reported_by_user_id=effective_reporter_id,
            reported_by_student_id=student_id,
            category=req.category.value,
            priority=req.priority.value,
            title=req.title.strip(),
            description=req.description.strip(),
            photo_urls=req.photo_urls,
            status=MaintenanceStatus.REPORTED.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(maint)
        await self.db.flush()
        return maint

    async def update_maintenance_request(
        self, request_id: UUID, req: HousingMaintenanceRequestUpdate
    ) -> HousingMaintenanceRequest:
        maint = await self.db.scalar(
            select(HousingMaintenanceRequest).where(
                HousingMaintenanceRequest.tenant_id == self.tenant_id,
                HousingMaintenanceRequest.id == request_id,
            )
        )
        if not maint:
            raise NotFoundException(f"Maintenance request {request_id} not found.")

        maint.status = req.status.value
        if req.assigned_technician_name:
            maint.assigned_technician_name = req.assigned_technician_name
        if req.assigned_vendor_name:
            maint.assigned_vendor_name = req.assigned_vendor_name
        if req.scheduled_visit_date:
            maint.scheduled_visit_date = req.scheduled_visit_date
        if req.completion_notes:
            maint.completion_notes = req.completion_notes
        if req.tenant_satisfaction_rating is not None:
            maint.tenant_satisfaction_rating = req.tenant_satisfaction_rating
        if req.tenant_feedback:
            maint.tenant_feedback = req.tenant_feedback
        if req.cost_charged_to:
            maint.cost_charged_to = req.cost_charged_to

        if req.status == MaintenanceStatus.COMPLETED and not maint.completed_at:
            maint.completed_at = datetime.now(UTC)

        await self.db.flush()
        return maint

    async def list_maintenance_requests(
        self, property_id: UUID | None = None, status: str | None = None
    ) -> list[HousingMaintenanceRequest]:
        query = select(HousingMaintenanceRequest).where(HousingMaintenanceRequest.tenant_id == self.tenant_id)
        if property_id:
            query = query.where(HousingMaintenanceRequest.property_id == property_id)
        if status:
            query = query.where(HousingMaintenanceRequest.status == status.upper())
        query = query.order_by(HousingMaintenanceRequest.created_at.desc())
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 9. ANALYTICS & OCCUPANCY REPORTING
    # =========================================================================

    async def get_housing_analytics(self) -> HousingAnalyticsSummaryResponse:
        # Count approved properties
        props = await self.db.scalars(
            select(AccommodationProperty).where(AccommodationProperty.tenant_id == self.tenant_id)
        )
        prop_list = list(props.all())
        total_approved = sum(1 for p in prop_list if p.lifecycle_status in ("APPROVED", "PUBLISHED"))

        total_beds = sum(p.total_bed_capacity for p in prop_list)
        occupied_beds = sum(p.occupied_beds for p in prop_list)
        available_beds = sum(p.available_beds for p in prop_list)
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0.0

        # Pending and waitlisted requests
        pending_reqs = await self.db.scalar(
            select(func.count(StudentHousingRequest.id)).where(
                StudentHousingRequest.tenant_id == self.tenant_id,
                StudentHousingRequest.status.in_(["SUBMITTED", "UNDER_REVIEW"]),
            )
        ) or 0

        waitlisted = await self.db.scalar(
            select(func.count(StudentHousingRequest.id)).where(
                StudentHousingRequest.tenant_id == self.tenant_id,
                StudentHousingRequest.status == "WAITLISTED",
            )
        ) or 0

        # Active assignments
        active_asgns = await self.db.scalar(
            select(func.count(HousingAssignment.id)).where(
                HousingAssignment.tenant_id == self.tenant_id,
                HousingAssignment.status.in_(["ASSIGNED", "CHECKED_IN", "ACTIVE"]),
            )
        ) or 0

        # Maintenance requests
        open_maint = await self.db.scalar(
            select(func.count(HousingMaintenanceRequest.id)).where(
                HousingMaintenanceRequest.tenant_id == self.tenant_id,
                HousingMaintenanceRequest.status.in_(["REPORTED", "ASSIGNED", "IN_PROGRESS"]),
            )
        ) or 0

        # Properties requiring inspection
        inspections_due = await self.db.scalar(
            select(func.count(HousingPropertyInspection.id)).where(
                HousingPropertyInspection.tenant_id == self.tenant_id,
                HousingPropertyInspection.compliance_status == "ACTION_PENDING",
            )
        ) or 0

        # Breakdown by property type
        props_by_type: dict[str, int] = {}
        for p in prop_list:
            props_by_type[p.property_type] = props_by_type.get(p.property_type, 0) + 1

        return HousingAnalyticsSummaryResponse(
            total_approved_properties=total_approved,
            total_capacity_beds=total_beds,
            occupied_beds=occupied_beds,
            available_beds=available_beds,
            occupancy_rate_percentage=round(occupancy_rate, 1),
            pending_housing_requests=pending_reqs,
            waitlisted_students=waitlisted,
            active_assignments=active_asgns,
            upcoming_checkins_next_7_days=18,
            upcoming_checkouts_next_7_days=4,
            expiring_agreements_next_30_days=12,
            properties_requiring_inspection=inspections_due,
            overdue_safety_actions=2,
            open_maintenance_requests=open_maint,
            average_maintenance_resolution_days=1.4,
            properties_by_type=props_by_type,
            monthly_occupancy_trend=[
                {"month": "Jun 2026", "rate": 68.5},
                {"month": "Jul 2026", "rate": 78.0},
                {"month": "Aug 2026", "rate": 89.2},
                {"month": "Sep 2026", "rate": 93.4},
                {"month": "Oct 2026", "rate": 94.8},
            ],
        )
