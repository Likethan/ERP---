"""CampusOS Enterprise Transport, Fleet, Routes & Student Mobility Service (Step 55).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Integrates with:
- Asset Management (authoritative vehicle asset registry, maintenance work orders, defect logs)
- Workforce (authoritative driver profiles, employee records, schedule conflicts)
- Finance (authoritative transport invoices, line items, fee plans, reconciliation)
- Core (Campuses, Institutions, Academic Years)
- People (Students, Users, Staff)
- Notifications & Outbox Events (Transactional Event Backbone)
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import DomainEventType, event_publisher
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assets import (
    Asset,
    AssetCategory,
    MaintenanceOperationalImpact,
    MaintenanceOrderStatus,
    MaintenancePriority,
    MaintenanceSeverity,
    MaintenanceWorkOrder,
)
from app.models.finance import FeeCategory, Invoice, InvoiceLineItem
from app.models.people import StudentProfile
from app.models.transport import (
    BoardingStatus,
    DriverStatus,
    IncidentStatus,
    RouteStatus,
    TrackingProviderStatus,
    TransportAllocation,
    TransportAllocationStatus,
    TransportApplication,
    TransportApplicationStatus,
    TransportBoardingRecord,
    TransportDriver,
    TransportFeePlan,
    TransportFeeStatus,
    TransportFuelLog,
    TransportIncident,
    TransportLocationSnapshot,
    TransportRoute,
    TransportServiceConfig,
    TransportStop,
    TransportTrackingSource,
    TransportTrip,
    TransportVehicle,
    TransportWaitlist,
    TripStatus,
    VehicleStatus,
    VerificationMethod,
    VerificationStatus,
    WaitlistStatus,
)
from app.schemas.transport import (
    BatchAllocationCandidate,
    BatchAllocationCommitRequest,
    BatchAllocationCommitResponse,
    BatchAllocationPreviewRequest,
    BatchAllocationPreviewResponse,
    DriverComplianceStatusResponse,
    GenerateTransportInvoiceRequest,
    GenerateTransportInvoiceResponse,
    RouteUtilizationReportItem,
    TransportAllocationCreate,
    TransportAllocationResponse,
    TransportAllocationTransferRequest,
    TransportApplicationCreate,
    TransportApplicationReviewRequest,
    TransportBoardingRecordResponse,
    TransportBoardingVerifyRequest,
    TransportDashboardResponse,
    TransportDriverCreate,
    TransportDriverUpdate,
    TransportFeePlanCreate,
    TransportFuelLogCreate,
    TransportIncidentCreate,
    TransportIncidentUpdate,
    TransportLiveTrackingResponse,
    TransportLocationPingRequest,
    TransportRouteCreate,
    TransportRouteUpdate,
    TransportServiceConfigCreate,
    TransportServiceConfigUpdate,
    TransportStopCreate,
    TransportStopUpdate,
    TransportTrackingSourceConfig,
    TransportTripCreate,
    TransportTripDispatch,
    TransportTripResponse,
    TransportVehicleCreate,
    TransportVehicleUpdate,
    TripManifestResponse,
    VehicleComplianceStatusResponse,
)


class TransportService:
    """Enterprise Transport and Fleet Management Service Layer."""

    # =========================================================================
    # 1. SERVICE CONFIGURATION
    # =========================================================================

    @staticmethod
    async def create_service_config(
        db: AsyncSession, tenant_id: UUID, payload: TransportServiceConfigCreate
    ) -> TransportServiceConfig:
        existing = await db.scalar(
            select(TransportServiceConfig).where(
                TransportServiceConfig.tenant_id == tenant_id,
                TransportServiceConfig.service_code == payload.service_code,
            )
        )
        if existing:
            raise ConflictException(
                f"Transport service configuration with code '{payload.service_code}' already exists."
            )

        config = TransportServiceConfig(
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            service_code=payload.service_code,
            service_name=payload.service_name,
            academic_year_id=payload.academic_year_id,
            zone_code=payload.zone_code,
            operating_period_start=payload.operating_period_start,
            operating_period_end=payload.operating_period_end,
            eligibility_criteria=payload.eligibility_criteria,
            capacity_policy=payload.capacity_policy,
            is_active=payload.is_active,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def get_service_config(
        db: AsyncSession, tenant_id: UUID, config_id: UUID
    ) -> TransportServiceConfig:
        config = await db.scalar(
            select(TransportServiceConfig).where(
                TransportServiceConfig.tenant_id == tenant_id,
                TransportServiceConfig.id == config_id,
            )
        )
        if not config:
            raise NotFoundException("Transport service configuration not found.")
        return config

    @staticmethod
    async def update_service_config(
        db: AsyncSession,
        tenant_id: UUID,
        config_id: UUID,
        payload: TransportServiceConfigUpdate,
    ) -> TransportServiceConfig:
        config = await TransportService.get_service_config(db, tenant_id, config_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def list_service_configs(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> list[TransportServiceConfig]:
        stmt = select(TransportServiceConfig).where(
            TransportServiceConfig.tenant_id == tenant_id
        )
        if campus_id:
            stmt = stmt.where(TransportServiceConfig.campus_id == campus_id)
        if is_active is not None:
            stmt = stmt.where(TransportServiceConfig.is_active == is_active)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 2. VEHICLE & FLEET REGISTRY
    # =========================================================================

    @staticmethod
    async def create_vehicle(
        db: AsyncSession, tenant_id: UUID, payload: TransportVehicleCreate
    ) -> TransportVehicle:
        reg_num = payload.registration_number.strip().upper()
        existing = await db.scalar(
            select(TransportVehicle).where(
                TransportVehicle.tenant_id == tenant_id,
                TransportVehicle.registration_number == reg_num,
            )
        )
        if existing:
            raise ConflictException(
                f"Vehicle with registration number '{reg_num}' is already registered in this institution."
            )

        asset_id = payload.asset_id
        if asset_id:
            asset = await db.scalar(
                select(Asset).where(
                    Asset.tenant_id == tenant_id, Asset.id == asset_id
                )
            )
            if not asset:
                raise NotFoundException("Linked physical asset record not found.")
        else:
            # Auto-link or auto-provision Asset record for vehicle maintenance integration
            cat = await db.scalar(
                select(AssetCategory).where(
                    AssetCategory.tenant_id == tenant_id,
                    AssetCategory.code == "VEHICLE",
                )
            )
            if not cat:
                cat = AssetCategory(
                    tenant_id=tenant_id,
                    code="VEHICLE",
                    name="Institutional Vehicle Fleet",
                )
                db.add(cat)
                await db.flush()

            asset = Asset(
                tenant_id=tenant_id,
                asset_tag=f"AST-FLT-{uuid.uuid4().hex[:6].upper()}",
                name=f"{payload.make or 'Fleet'} {payload.model or 'Vehicle'} ({reg_num})",
                category_id=cat.id,
                campus_id=payload.campus_id,
                acquisition_date=date.today(),
            )
            db.add(asset)
            await db.flush()
            asset_id = asset.id

        vehicle = TransportVehicle(
            tenant_id=tenant_id,
            asset_id=asset_id,
            campus_id=payload.campus_id,
            registration_number=reg_num,
            fleet_identifier=payload.fleet_identifier,
            vehicle_category=payload.vehicle_category.value
            if hasattr(payload.vehicle_category, "value")
            else str(payload.vehicle_category),
            make=payload.make,
            model=payload.model,
            manufacturing_year=payload.manufacturing_year,
            capacity=payload.capacity,
            accessible_seating_capacity=payload.accessible_seating_capacity,
            permitted_passenger_capacity=payload.permitted_passenger_capacity
            or payload.capacity,
            insurance_policy_number=payload.insurance_policy_number,
            insurance_expiry=payload.insurance_expiry,
            fitness_certificate_number=payload.fitness_certificate_number,
            fitness_certificate_expiry=payload.fitness_certificate_expiry,
            permit_number=payload.permit_number,
            permit_expiry=payload.permit_expiry,
            pollution_certificate_expiry=payload.pollution_certificate_expiry,
            fuel_type=payload.fuel_type.value
            if hasattr(payload.fuel_type, "value")
            else str(payload.fuel_type),
            operational_depot=payload.operational_depot,
            status=payload.status.value
            if hasattr(payload.status, "value")
            else str(payload.status),
            current_odometer_km=payload.current_odometer_km,
            safety_equipment_details=payload.safety_equipment_details
            or {
                "fire_extinguisher": True,
                "first_aid_kit": True,
                "emergency_exit": True,
            },
            is_active=payload.is_active,
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        return vehicle

    @staticmethod
    async def get_vehicle(
        db: AsyncSession, tenant_id: UUID, vehicle_id: UUID
    ) -> TransportVehicle:
        vehicle = await db.scalar(
            select(TransportVehicle).where(
                TransportVehicle.tenant_id == tenant_id,
                TransportVehicle.id == vehicle_id,
            )
        )
        if not vehicle:
            raise NotFoundException("Fleet vehicle record not found.")
        return vehicle

    @staticmethod
    async def update_vehicle(
        db: AsyncSession,
        tenant_id: UUID,
        vehicle_id: UUID,
        payload: TransportVehicleUpdate,
    ) -> TransportVehicle:
        vehicle = await TransportService.get_vehicle(db, tenant_id, vehicle_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(value, "value"):
                setattr(vehicle, key, value.value)
            else:
                setattr(vehicle, key, value)
        await db.commit()
        await db.refresh(vehicle)
        return vehicle

    @staticmethod
    async def list_vehicles(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        status: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[TransportVehicle]:
        stmt = select(TransportVehicle).where(TransportVehicle.tenant_id == tenant_id)
        if campus_id:
            stmt = stmt.where(TransportVehicle.campus_id == campus_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportVehicle.status == status)
        if category and category != "ALL":
            stmt = stmt.where(TransportVehicle.vehicle_category == category)
        if search and search.strip():
            q = f"%{search.strip().upper()}%"
            stmt = stmt.where(
                or_(
                    TransportVehicle.registration_number.ilike(q),
                    TransportVehicle.fleet_identifier.ilike(q),
                    TransportVehicle.make.ilike(q),
                    TransportVehicle.model.ilike(q),
                )
            )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_vehicle_compliance(
        db: AsyncSession, tenant_id: UUID, vehicle_id: UUID
    ) -> VehicleComplianceStatusResponse:
        vehicle = await TransportService.get_vehicle(db, tenant_id, vehicle_id)
        today = date.today()
        remarks: list[str] = []
        is_compliant = True

        is_ins_expired = vehicle.insurance_expiry < today
        if is_ins_expired:
            remarks.append(
                f"Insurance expired on {vehicle.insurance_expiry.isoformat()}."
            )
            is_compliant = False

        is_fit_expired = vehicle.fitness_certificate_expiry < today
        if is_fit_expired:
            remarks.append(
                f"Fitness certificate expired on {vehicle.fitness_certificate_expiry.isoformat()}."
            )
            is_compliant = False

        is_permit_expired = False
        if vehicle.permit_expiry and vehicle.permit_expiry < today:
            is_permit_expired = True
            remarks.append(f"Permit expired on {vehicle.permit_expiry.isoformat()}.")
            is_compliant = False

        if vehicle.status == VehicleStatus.MAINTENANCE.value:
            remarks.append("Vehicle is currently under maintenance.")
            is_compliant = False
        elif vehicle.status != VehicleStatus.ACTIVE.value:
            remarks.append(f"Vehicle status is {vehicle.status}.")
            is_compliant = False

        return VehicleComplianceStatusResponse(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            status=VehicleStatus(vehicle.status),
            insurance_expiry=vehicle.insurance_expiry,
            is_insurance_expired=is_ins_expired,
            fitness_certificate_expiry=vehicle.fitness_certificate_expiry,
            is_fitness_expired=is_fit_expired,
            permit_expiry=vehicle.permit_expiry,
            is_permit_expired=is_permit_expired,
            is_compliant_for_dispatch=is_compliant,
            compliance_remarks=remarks,
        )

    # =========================================================================
    # 3. DRIVER & PERSONNEL MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_driver(
        db: AsyncSession, tenant_id: UUID, payload: TransportDriverCreate
    ) -> TransportDriver:
        lic_num = payload.license_number.strip().upper()
        existing = await db.scalar(
            select(TransportDriver).where(
                TransportDriver.tenant_id == tenant_id,
                TransportDriver.license_number == lic_num,
            )
        )
        if existing:
            raise ConflictException(
                f"Driver with license number '{lic_num}' already exists in this institution."
            )

        driver = TransportDriver(
            tenant_id=tenant_id,
            user_id=payload.user_id,
            employee_id=payload.employee_id,
            full_name=payload.full_name.strip(),
            license_number=lic_num,
            license_categories=payload.license_categories or ["HEAVY_PASSENGER", "BUS"],
            license_expiry=payload.license_expiry,
            phone_number=payload.phone_number.strip(),
            email=payload.email,
            badge_number=payload.badge_number,
            badge_expiry=payload.badge_expiry,
            certifications=payload.certifications or {"defensive_driving": True},
            background_verification_status=payload.background_verification_status.value
            if hasattr(payload.background_verification_status, "value")
            else str(payload.background_verification_status),
            shift_preference=payload.shift_preference,
            status=payload.status.value
            if hasattr(payload.status, "value")
            else str(payload.status),
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            is_active=payload.is_active,
        )
        db.add(driver)
        await db.commit()
        await db.refresh(driver)
        return driver

    @staticmethod
    async def get_driver(
        db: AsyncSession, tenant_id: UUID, driver_id: UUID
    ) -> TransportDriver:
        driver = await db.scalar(
            select(TransportDriver).where(
                TransportDriver.tenant_id == tenant_id,
                TransportDriver.id == driver_id,
            )
        )
        if not driver:
            raise NotFoundException("Driver profile record not found.")
        return driver

    @staticmethod
    async def update_driver(
        db: AsyncSession,
        tenant_id: UUID,
        driver_id: UUID,
        payload: TransportDriverUpdate,
    ) -> TransportDriver:
        driver = await TransportService.get_driver(db, tenant_id, driver_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(value, "value"):
                setattr(driver, key, value.value)
            else:
                setattr(driver, key, value)
        await db.commit()
        await db.refresh(driver)
        return driver

    @staticmethod
    async def list_drivers(
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        search: str | None = None,
    ) -> list[TransportDriver]:
        stmt = select(TransportDriver).where(TransportDriver.tenant_id == tenant_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportDriver.status == status)
        if search and search.strip():
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    TransportDriver.full_name.ilike(q),
                    TransportDriver.license_number.ilike(q),
                    TransportDriver.phone_number.ilike(q),
                )
            )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_driver_compliance(
        db: AsyncSession, tenant_id: UUID, driver_id: UUID
    ) -> DriverComplianceStatusResponse:
        driver = await TransportService.get_driver(db, tenant_id, driver_id)
        today = date.today()
        remarks: list[str] = []
        is_compliant = True

        is_lic_expired = driver.license_expiry < today
        if is_lic_expired:
            remarks.append(
                f"Driving license expired on {driver.license_expiry.isoformat()}."
            )
            is_compliant = False

        if (
            driver.background_verification_status
            != VerificationStatus.VERIFIED.value
        ):
            remarks.append(
                f"Background verification status is {driver.background_verification_status}."
            )
            is_compliant = False

        if driver.status != DriverStatus.ACTIVE.value:
            remarks.append(f"Driver status is {driver.status}.")
            is_compliant = False

        return DriverComplianceStatusResponse(
            driver_id=driver.id,
            full_name=driver.full_name,
            license_number=driver.license_number,
            status=DriverStatus(driver.status),
            license_expiry=driver.license_expiry,
            is_license_expired=is_lic_expired,
            background_verification_status=VerificationStatus(
                driver.background_verification_status
            ),
            is_compliant_for_dispatch=is_compliant,
            compliance_remarks=remarks,
        )

    # =========================================================================
    # 4. ROUTE & STOP MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_route(
        db: AsyncSession, tenant_id: UUID, payload: TransportRouteCreate
    ) -> TransportRoute:
        code = payload.route_code.strip().upper()
        existing = await db.scalar(
            select(TransportRoute).where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.route_code == code,
            )
        )
        if existing:
            raise ConflictException(f"Route with code '{code}' already exists.")

        route = TransportRoute(
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            route_code=code,
            route_name=payload.route_name.strip(),
            description=payload.description,
            start_point=payload.start_point.strip(),
            end_point=payload.end_point.strip(),
            distance_km=payload.distance_km,
            estimated_duration_minutes=payload.estimated_duration_minutes,
            morning_departure_time=payload.morning_departure_time,
            evening_return_time=payload.evening_return_time,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            capacity=payload.capacity,
            allocated_students=0,
            direction=payload.direction.value
            if hasattr(payload.direction, "value")
            else str(payload.direction),
            status=payload.status.value
            if hasattr(payload.status, "value")
            else str(payload.status),
            is_active=payload.is_active,
        )
        db.add(route)
        await db.flush()

        if payload.stops:
            for s_in in payload.stops:
                stop = TransportStop(
                    tenant_id=tenant_id,
                    route_id=route.id,
                    stop_name=s_in.stop_name.strip(),
                    stop_code=s_in.stop_code,
                    stop_sequence=s_in.stop_sequence,
                    address=s_in.address,
                    landmark=s_in.landmark,
                    latitude=s_in.latitude,
                    longitude=s_in.longitude,
                    pickup_time=s_in.pickup_time,
                    drop_time=s_in.drop_time,
                    fare_annual=s_in.fare_annual,
                    fare_term=s_in.fare_term,
                    fare_monthly=s_in.fare_monthly,
                    max_boarding_capacity=s_in.max_boarding_capacity,
                    is_active=s_in.is_active,
                )
                db.add(stop)

        await db.commit()
        await db.refresh(route)
        return route

    @staticmethod
    async def get_route(
        db: AsyncSession, tenant_id: UUID, route_id: UUID
    ) -> TransportRoute:
        route = await db.scalar(
            select(TransportRoute)
            .options(
                selectinload(TransportRoute.stops),
                selectinload(TransportRoute.vehicle),
                selectinload(TransportRoute.driver),
            )
            .where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.id == route_id,
            )
        )
        if not route:
            raise NotFoundException("Transport route record not found.")
        return route

    @staticmethod
    async def update_route(
        db: AsyncSession,
        tenant_id: UUID,
        route_id: UUID,
        payload: TransportRouteUpdate,
    ) -> TransportRoute:
        route = await TransportService.get_route(db, tenant_id, route_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(value, "value"):
                setattr(route, key, value.value)
            else:
                setattr(route, key, value)
        await db.commit()
        await db.refresh(route)
        return route

    @staticmethod
    async def list_routes(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[TransportRoute]:
        stmt = (
            select(TransportRoute)
            .options(
                selectinload(TransportRoute.stops),
                selectinload(TransportRoute.vehicle),
                selectinload(TransportRoute.driver),
            )
            .where(TransportRoute.tenant_id == tenant_id)
        )
        if campus_id:
            stmt = stmt.where(TransportRoute.campus_id == campus_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportRoute.status == status)
        if search and search.strip():
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    TransportRoute.route_code.ilike(q),
                    TransportRoute.route_name.ilike(q),
                    TransportRoute.start_point.ilike(q),
                    TransportRoute.end_point.ilike(q),
                )
            )
        stmt = stmt.order_by(TransportRoute.route_code.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_stop(
        db: AsyncSession,
        tenant_id: UUID,
        route_id: UUID,
        payload: TransportStopCreate,
    ) -> TransportStop:
        # Validate route exists
        await TransportService.get_route(db, tenant_id, route_id)

        stop = TransportStop(
            tenant_id=tenant_id,
            route_id=route_id,
            stop_name=payload.stop_name.strip(),
            stop_code=payload.stop_code,
            stop_sequence=payload.stop_sequence,
            address=payload.address,
            landmark=payload.landmark,
            latitude=payload.latitude,
            longitude=payload.longitude,
            pickup_time=payload.pickup_time,
            drop_time=payload.drop_time,
            fare_annual=payload.fare_annual,
            fare_term=payload.fare_term,
            fare_monthly=payload.fare_monthly,
            max_boarding_capacity=payload.max_boarding_capacity,
            is_active=payload.is_active,
        )
        db.add(stop)
        await db.commit()
        await db.refresh(stop)
        return stop

    @staticmethod
    async def update_stop(
        db: AsyncSession,
        tenant_id: UUID,
        route_id: UUID,
        stop_id: UUID,
        payload: TransportStopUpdate,
    ) -> TransportStop:
        stop = await db.scalar(
            select(TransportStop).where(
                TransportStop.route_id == route_id, TransportStop.id == stop_id
            )
        )
        if not stop:
            raise NotFoundException("Transport stop record not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stop, key, value)
        await db.commit()
        await db.refresh(stop)
        return stop

    @staticmethod
    async def list_stops(
        db: AsyncSession, tenant_id: UUID, route_id: UUID
    ) -> list[TransportStop]:
        await TransportService.get_route(db, tenant_id, route_id)
        stmt = (
            select(TransportStop)
            .where(TransportStop.route_id == route_id)
            .order_by(TransportStop.stop_sequence.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 5. STUDENT APPLICATIONS & SUBSCRIPTIONS
    # =========================================================================

    @staticmethod
    async def submit_application(
        db: AsyncSession, tenant_id: UUID, payload: TransportApplicationCreate
    ) -> TransportApplication:
        # Validate student
        student = await db.scalar(
            select(StudentProfile).where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.id == payload.student_id,
            )
        )
        if not student:
            raise NotFoundException("Student enrollment profile not found.")

        # Check existing active or submitted application for same year
        existing = await db.scalar(
            select(TransportApplication).where(
                TransportApplication.tenant_id == tenant_id,
                TransportApplication.student_id == payload.student_id,
                TransportApplication.academic_year_id == payload.academic_year_id,
                TransportApplication.status.in_(
                    [
                        TransportApplicationStatus.SUBMITTED.value,
                        TransportApplicationStatus.UNDER_REVIEW.value,
                        TransportApplicationStatus.APPROVED.value,
                    ]
                ),
            )
        )
        if existing:
            raise ConflictException(
                "An active transport application already exists for this student in this academic year."
            )

        count = (
            await db.scalar(
                select(func.count(TransportApplication.id)).where(
                    TransportApplication.tenant_id == tenant_id
                )
            )
            or 0
        )
        app_num = f"TR-APP-{date.today().year}-{count + 1:05d}"

        app = TransportApplication(
            tenant_id=tenant_id,
            application_number=app_num,
            student_id=payload.student_id,
            academic_year_id=payload.academic_year_id,
            preferred_route_id=payload.preferred_route_id,
            preferred_stop_id=payload.preferred_stop_id,
            service_type=payload.service_type.value
            if hasattr(payload.service_type, "value")
            else str(payload.service_type),
            status=TransportApplicationStatus.SUBMITTED.value,
            priority_score=payload.priority_score,
            accessibility_needed=payload.accessibility_needed,
            special_requests=payload.special_requests,
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_APPLICATION_SUBMITTED,
            aggregate_type="TransportApplication",
            aggregate_id=app.id,
            payload={
                "application_id": str(app.id),
                "student_id": str(app.student_id),
                "preferred_route_id": str(app.preferred_route_id),
                "preferred_stop_id": str(app.preferred_stop_id),
                "service_type": app.service_type,
            },
        )
        return app

    @staticmethod
    async def review_application(
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        payload: TransportApplicationReviewRequest,
        reviewer_id: UUID,
    ) -> TransportApplication:
        app = await db.scalar(
            select(TransportApplication).where(
                TransportApplication.tenant_id == tenant_id,
                TransportApplication.id == application_id,
            )
        )
        if not app:
            raise NotFoundException("Transport application not found.")

        target_status = (
            payload.status.value
            if hasattr(payload.status, "value")
            else str(payload.status)
        )
        app.status = target_status
        app.reviewer_user_id = reviewer_id
        app.reviewed_at = datetime.now(UTC)
        if payload.rejection_reason:
            app.rejection_reason = payload.rejection_reason

        # If approved, automatically confirm allocation or put in waitlist if full
        if target_status == TransportApplicationStatus.APPROVED.value:
            route = await TransportService.get_route(
                db, tenant_id, app.preferred_route_id
            )
            active_count = (
                await db.scalar(
                    select(func.count(TransportAllocation.id)).where(
                        TransportAllocation.tenant_id == tenant_id,
                        TransportAllocation.route_id == route.id,
                        TransportAllocation.status.in_(
                            [
                                TransportAllocationStatus.ACTIVE.value,
                                TransportAllocationStatus.RESERVED.value,
                            ]
                        ),
                    )
                )
                or 0
            )

            effective_capacity = route.capacity
            if route.vehicle and route.vehicle.capacity < effective_capacity:
                effective_capacity = route.vehicle.capacity

            if active_count >= effective_capacity:
                # Add to waitlist
                wl_count = (
                    await db.scalar(
                        select(func.count(TransportWaitlist.id)).where(
                            TransportWaitlist.tenant_id == tenant_id,
                            TransportWaitlist.route_id == route.id,
                            TransportWaitlist.status == WaitlistStatus.WAITING.value,
                        )
                    )
                    or 0
                )
                waitlist_entry = TransportWaitlist(
                    tenant_id=tenant_id,
                    route_id=route.id,
                    stop_id=app.preferred_stop_id,
                    student_id=app.student_id,
                    application_id=app.id,
                    priority_score=app.priority_score,
                    queue_position=wl_count + 1,
                    status=WaitlistStatus.WAITING.value,
                )
                db.add(waitlist_entry)
                app.status = TransportApplicationStatus.WAITLISTED.value
            else:
                # Confirm allocation
                alloc_count = (
                    await db.scalar(
                        select(func.count(TransportAllocation.id)).where(
                            TransportAllocation.tenant_id == tenant_id
                        )
                    )
                    or 0
                )
                pass_num = f"TR-PASS-{date.today().year}-{alloc_count + 1:05d}"
                allocation = TransportAllocation(
                    tenant_id=tenant_id,
                    pass_number=pass_num,
                    student_id=app.student_id,
                    academic_year_id=app.academic_year_id,
                    route_id=app.preferred_route_id,
                    stop_id=app.preferred_stop_id,
                    vehicle_id=route.vehicle_id,
                    service_type=app.service_type,
                    seat_number=payload.assigned_seat_number,
                    status=TransportAllocationStatus.ACTIVE.value,
                    valid_from=date.today(),
                    fee_status=TransportFeeStatus.PENDING.value,
                    is_active=True,
                )
                db.add(allocation)
                route.allocated_students = active_count + 1

                await event_publisher.publish(
                    db=db,
                    tenant_id=tenant_id,
                    event_type=DomainEventType.TRANSPORT_ALLOCATION_CONFIRMED,
                    aggregate_type="TransportAllocation",
                    aggregate_id=allocation.id,
                    payload={
                        "allocation_id": str(allocation.id),
                        "student_id": str(allocation.student_id),
                        "route_id": str(allocation.route_id),
                        "stop_id": str(allocation.stop_id),
                        "vehicle_id": str(allocation.vehicle_id)
                        if allocation.vehicle_id
                        else "",
                        "pass_number": allocation.pass_number,
                    },
                )

        await db.commit()
        await db.refresh(app)
        return app

    @staticmethod
    async def list_applications(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        route_id: UUID | None = None,
        status: str | None = None,
    ) -> list[TransportApplication]:
        stmt = select(TransportApplication).where(
            TransportApplication.tenant_id == tenant_id
        )
        if student_id:
            stmt = stmt.where(TransportApplication.student_id == student_id)
        if route_id:
            stmt = stmt.where(TransportApplication.preferred_route_id == route_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportApplication.status == status)
        stmt = stmt.order_by(TransportApplication.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_waitlist(
        db: AsyncSession,
        tenant_id: UUID,
        route_id: UUID | None = None,
        status: str | None = None,
    ) -> list[TransportWaitlist]:
        stmt = select(TransportWaitlist).where(TransportWaitlist.tenant_id == tenant_id)
        if route_id:
            stmt = stmt.where(TransportWaitlist.route_id == route_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportWaitlist.status == status)
        stmt = stmt.order_by(TransportWaitlist.queue_position.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 6. SEAT ALLOCATION & CONCURRENCY-SAFE CAPACITY MANAGEMENT
    # =========================================================================

    @staticmethod
    async def allocate_passenger(
        db: AsyncSession, tenant_id: UUID, payload: TransportAllocationCreate
    ) -> TransportAllocation:
        # Check student does not already have an active pass
        existing = await db.scalar(
            select(TransportAllocation).where(
                TransportAllocation.tenant_id == tenant_id,
                TransportAllocation.student_id == payload.student_id,
                TransportAllocation.academic_year_id == payload.academic_year_id,
                TransportAllocation.status.in_(
                    [
                        TransportAllocationStatus.ACTIVE.value,
                        TransportAllocationStatus.RESERVED.value,
                    ]
                ),
            )
        )
        if existing:
            raise ConflictException(
                "Student already has an active or reserved transport allocation for this academic year."
            )

        # Concurrency safety: lock the route row
        route_stmt = (
            select(TransportRoute)
            .where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.id == payload.route_id,
            )
            .with_for_update()
        )
        route = await db.scalar(route_stmt)
        if not route:
            raise NotFoundException("Target transit route not found.")

        active_count = (
            await db.scalar(
                select(func.count(TransportAllocation.id)).where(
                    TransportAllocation.tenant_id == tenant_id,
                    TransportAllocation.route_id == payload.route_id,
                    TransportAllocation.status.in_(
                        [
                            TransportAllocationStatus.ACTIVE.value,
                            TransportAllocationStatus.RESERVED.value,
                        ]
                    ),
                )
            )
            or 0
        )

        effective_capacity = route.capacity
        if payload.vehicle_id:
            vehicle = await TransportService.get_vehicle(
                db, tenant_id, payload.vehicle_id
            )
            effective_capacity = min(effective_capacity, vehicle.capacity)
        elif route.vehicle_id:
            vehicle = await db.scalar(
                select(TransportVehicle).where(
                    TransportVehicle.tenant_id == tenant_id,
                    TransportVehicle.id == route.vehicle_id,
                )
            )
            if vehicle:
                effective_capacity = min(effective_capacity, vehicle.capacity)

        if active_count >= effective_capacity:
            raise ConflictException(
                f"Route '{route.route_name}' capacity limit reached ({active_count}/{effective_capacity}). Overbooking is prohibited."
            )

        # Verify stop belongs to route
        stop = await db.scalar(
            select(TransportStop).where(
                TransportStop.route_id == payload.route_id,
                TransportStop.id == payload.stop_id,
            )
        )
        if not stop:
            raise BadRequestException("Selected stop does not belong to this route.")

        alloc_count = (
            await db.scalar(
                select(func.count(TransportAllocation.id)).where(
                    TransportAllocation.tenant_id == tenant_id
                )
            )
            or 0
        )
        pass_num = f"TR-PASS-{date.today().year}-{alloc_count + 1:05d}"

        allocation = TransportAllocation(
            tenant_id=tenant_id,
            pass_number=pass_num,
            student_id=payload.student_id,
            academic_year_id=payload.academic_year_id,
            route_id=payload.route_id,
            stop_id=payload.stop_id,
            vehicle_id=payload.vehicle_id or route.vehicle_id,
            service_type=payload.service_type.value
            if hasattr(payload.service_type, "value")
            else str(payload.service_type),
            seat_number=payload.seat_number,
            status=TransportAllocationStatus.ACTIVE.value,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            fee_status=TransportFeeStatus.PENDING.value,
            is_active=True,
        )
        db.add(allocation)
        route.allocated_students = active_count + 1

        await db.commit()
        await db.refresh(allocation)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_ALLOCATION_CONFIRMED,
            aggregate_type="TransportAllocation",
            aggregate_id=allocation.id,
            payload={
                "allocation_id": str(allocation.id),
                "student_id": str(allocation.student_id),
                "route_id": str(allocation.route_id),
                "stop_id": str(allocation.stop_id),
                "pass_number": allocation.pass_number,
            },
        )
        return allocation

    @staticmethod
    async def cancel_allocation(
        db: AsyncSession,
        tenant_id: UUID,
        allocation_id: UUID,
        cancellation_reason: str | None = None,
    ) -> TransportAllocation:
        alloc = await db.scalar(
            select(TransportAllocation).where(
                TransportAllocation.tenant_id == tenant_id,
                TransportAllocation.id == allocation_id,
            )
        )
        if not alloc:
            raise NotFoundException("Transport pass allocation not found.")

        alloc.status = TransportAllocationStatus.CANCELLED.value
        alloc.is_active = False

        # Decrement route counter
        route = await db.scalar(
            select(TransportRoute).where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.id == alloc.route_id,
            )
        )
        if route and route.allocated_students > 0:
            route.allocated_students -= 1

        await db.commit()
        await db.refresh(alloc)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_ALLOCATION_CANCELLED,
            aggregate_type="TransportAllocation",
            aggregate_id=alloc.id,
            payload={
                "allocation_id": str(alloc.id),
                "student_id": str(alloc.student_id),
                "route_id": str(alloc.route_id),
                "cancellation_reason": cancellation_reason or "Cancelled by user/officer",
            },
        )
        return alloc

    @staticmethod
    async def transfer_allocation(
        db: AsyncSession,
        tenant_id: UUID,
        allocation_id: UUID,
        payload: TransportAllocationTransferRequest,
    ) -> TransportAllocation:
        alloc = await db.scalar(
            select(TransportAllocation).where(
                TransportAllocation.tenant_id == tenant_id,
                TransportAllocation.id == allocation_id,
                TransportAllocation.status == TransportAllocationStatus.ACTIVE.value,
            )
        )
        if not alloc:
            raise NotFoundException("Active transport allocation not found.")

        old_route = await db.scalar(
            select(TransportRoute).where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.id == alloc.route_id,
            )
        )

        new_route = await db.scalar(
            select(TransportRoute)
            .where(
                TransportRoute.tenant_id == tenant_id,
                TransportRoute.id == payload.new_route_id,
            )
            .with_for_update()
        )
        if not new_route:
            raise NotFoundException("Destination transit route not found.")

        # Check new route capacity
        active_count = (
            await db.scalar(
                select(func.count(TransportAllocation.id)).where(
                    TransportAllocation.tenant_id == tenant_id,
                    TransportAllocation.route_id == new_route.id,
                    TransportAllocation.status == TransportAllocationStatus.ACTIVE.value,
                )
            )
            or 0
        )
        if active_count >= new_route.capacity:
            raise ConflictException(
                f"Destination route capacity ({new_route.capacity}) is exhausted."
            )

        # Update allocation
        alloc.route_id = payload.new_route_id
        alloc.stop_id = payload.new_stop_id
        alloc.vehicle_id = new_route.vehicle_id
        if payload.new_seat_number:
            alloc.seat_number = payload.new_seat_number

        if old_route and old_route.allocated_students > 0:
            old_route.allocated_students -= 1
        new_route.allocated_students = active_count + 1

        await db.commit()
        await db.refresh(alloc)
        return alloc

    @staticmethod
    async def list_allocations(
        db: AsyncSession,
        tenant_id: UUID,
        route_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
    ) -> list[TransportAllocation]:
        stmt = select(TransportAllocation).where(
            TransportAllocation.tenant_id == tenant_id
        )
        if route_id:
            stmt = stmt.where(TransportAllocation.route_id == route_id)
        if student_id:
            stmt = stmt.where(TransportAllocation.student_id == student_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportAllocation.status == status)
        stmt = stmt.order_by(TransportAllocation.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_allocation(
        db: AsyncSession, tenant_id: UUID, allocation_id: UUID
    ) -> TransportAllocation:
        alloc = await db.scalar(
            select(TransportAllocation)
            .options(
                selectinload(TransportAllocation.route),
                selectinload(TransportAllocation.stop),
            )
            .where(
                TransportAllocation.tenant_id == tenant_id,
                TransportAllocation.id == allocation_id,
            )
        )
        if not alloc:
            raise NotFoundException("Transport pass allocation not found.")
        return alloc

    @staticmethod
    async def preview_batch_allocations(
        db: AsyncSession, tenant_id: UUID, payload: BatchAllocationPreviewRequest
    ) -> BatchAllocationPreviewResponse:
        stmt = (
            select(TransportApplication)
            .where(
                TransportApplication.tenant_id == tenant_id,
                TransportApplication.academic_year_id == payload.academic_year_id,
                TransportApplication.status.in_([
                    TransportApplicationStatus.SUBMITTED.value,
                    TransportApplicationStatus.WAITLISTED.value,
                ]),
            )
            .order_by(TransportApplication.priority_score.desc(), TransportApplication.created_at.asc())
        )
        if payload.route_id:
            stmt = stmt.where(TransportApplication.preferred_route_id == payload.route_id)

        applications = (await db.execute(stmt)).scalars().all()
        candidates: list[BatchAllocationCandidate] = []
        eligible_count = 0
        allocatable_count = 0
        waitlist_count = 0

        route_cache: dict[UUID, dict[str, int]] = {}

        for app in applications:
            r_id = app.preferred_route_id
            if r_id not in route_cache:
                route = await TransportService.get_route(db, tenant_id, r_id)
                active_count = (
                    await db.scalar(
                        select(func.count(TransportAllocation.id)).where(
                            TransportAllocation.tenant_id == tenant_id,
                            TransportAllocation.route_id == r_id,
                            TransportAllocation.status.in_([
                                TransportAllocationStatus.ACTIVE.value,
                                TransportAllocationStatus.RESERVED.value,
                            ]),
                        )
                    )
                    or 0
                )
                eff_cap = route.capacity
                if route.vehicle and route.vehicle.capacity < eff_cap:
                    eff_cap = route.vehicle.capacity
                route_cache[r_id] = {
                    "effective_capacity": eff_cap,
                    "allocated": active_count,
                }

            r_info = route_cache[r_id]
            eligible_count += 1
            if r_info["allocated"] < r_info["effective_capacity"]:
                r_info["allocated"] += 1
                allocatable_count += 1
                candidates.append(
                    BatchAllocationCandidate(
                        application_id=app.id,
                        student_id=app.student_id,
                        preferred_route_id=app.preferred_route_id,
                        preferred_stop_id=app.preferred_stop_id,
                        priority_score=app.priority_score,
                        can_allocate=True,
                        reason="Route capacity available based on priority score ranking",
                    )
                )
            else:
                waitlist_count += 1
                candidates.append(
                    BatchAllocationCandidate(
                        application_id=app.id,
                        student_id=app.student_id,
                        preferred_route_id=app.preferred_route_id,
                        preferred_stop_id=app.preferred_stop_id,
                        priority_score=app.priority_score,
                        can_allocate=False,
                        reason="Route capacity reached. Candidate queued for waitlist.",
                    )
                )

        return BatchAllocationPreviewResponse(
            route_id=payload.route_id,
            total_applications=len(applications),
            eligible_count=eligible_count,
            allocatable_count=allocatable_count,
            waitlist_count=waitlist_count,
            candidates=candidates,
        )

    @staticmethod
    async def commit_batch_allocations(
        db: AsyncSession,
        tenant_id: UUID,
        payload: BatchAllocationCommitRequest,
        actor_id: UUID,
    ) -> BatchAllocationCommitResponse:
        preview = await TransportService.preview_batch_allocations(
            db,
            tenant_id,
            BatchAllocationPreviewRequest(
                academic_year_id=payload.academic_year_id,
                route_id=payload.route_id,
            ),
        )

        allocations_created: list[TransportAllocation] = []
        allocated_count = 0
        waitlisted_count = 0

        target_app_ids = set(payload.application_ids) if payload.application_ids else None

        for cand in preview.candidates:
            if target_app_ids and cand.application_id not in target_app_ids:
                continue

            app = await db.scalar(
                select(TransportApplication).where(
                    TransportApplication.tenant_id == tenant_id,
                    TransportApplication.id == cand.application_id,
                )
            )
            if not app:
                continue

            if cand.can_allocate:
                app.status = TransportApplicationStatus.APPROVED.value
                app.reviewer_user_id = actor_id
                app.reviewed_at = datetime.now(UTC)

                route = await TransportService.get_route(db, tenant_id, app.preferred_route_id)
                alloc_count = (
                    await db.scalar(
                        select(func.count(TransportAllocation.id)).where(
                            TransportAllocation.tenant_id == tenant_id
                        )
                    )
                    or 0
                )
                pass_num = f"TR-PASS-{date.today().year}-{alloc_count + allocated_count + 1:05d}"
                allocation = TransportAllocation(
                    tenant_id=tenant_id,
                    pass_number=pass_num,
                    student_id=app.student_id,
                    academic_year_id=app.academic_year_id,
                    route_id=app.preferred_route_id,
                    stop_id=app.preferred_stop_id,
                    vehicle_id=route.vehicle_id,
                    service_type=app.service_type,
                    status=TransportAllocationStatus.ACTIVE.value,
                    valid_from=date.today(),
                    fee_status=TransportFeeStatus.PENDING.value,
                    is_active=True,
                )
                db.add(allocation)
                route.allocated_students += 1
                allocations_created.append(allocation)
                allocated_count += 1
            else:
                app.status = TransportApplicationStatus.WAITLISTED.value
                app.reviewer_user_id = actor_id
                app.reviewed_at = datetime.now(UTC)

                wl_count = (
                    await db.scalar(
                        select(func.count(TransportWaitlist.id)).where(
                            TransportWaitlist.tenant_id == tenant_id,
                            TransportWaitlist.route_id == app.preferred_route_id,
                            TransportWaitlist.status == WaitlistStatus.WAITING.value,
                        )
                    )
                    or 0
                )
                waitlist_entry = TransportWaitlist(
                    tenant_id=tenant_id,
                    route_id=app.preferred_route_id,
                    stop_id=app.preferred_stop_id,
                    student_id=app.student_id,
                    application_id=app.id,
                    priority_score=app.priority_score,
                    queue_position=wl_count + waitlisted_count + 1,
                    status=WaitlistStatus.WAITING.value,
                )
                db.add(waitlist_entry)
                waitlisted_count += 1

        await db.commit()
        for a in allocations_created:
            await db.refresh(a)

        return BatchAllocationCommitResponse(
            success=True,
            allocated_count=allocated_count,
            waitlisted_count=waitlisted_count,
            allocations=[TransportAllocationResponse.model_validate(a) for a in allocations_created],
        )

    # =========================================================================
    # 7. TRIP SCHEDULING, DISPATCH & OPERATIONAL DISRUPTIONS
    # =========================================================================

    @staticmethod
    async def schedule_trip(
        db: AsyncSession, tenant_id: UUID, payload: TransportTripCreate
    ) -> TransportTrip:
        route = await TransportService.get_route(db, tenant_id, payload.route_id)
        vehicle = await TransportService.get_vehicle(db, tenant_id, payload.vehicle_id)
        driver = await TransportService.get_driver(db, tenant_id, payload.driver_id)

        # 1. Compliance check: vehicle
        if vehicle.status == VehicleStatus.MAINTENANCE.value:
            raise ConflictException(
                f"Vehicle {vehicle.registration_number} is currently under maintenance."
            )
        if vehicle.insurance_expiry < payload.trip_date:
            raise ConflictException(
                f"Vehicle insurance expired on {vehicle.insurance_expiry.isoformat()}."
            )
        if vehicle.fitness_certificate_expiry < payload.trip_date:
            raise ConflictException(
                f"Vehicle fitness certificate expired on {vehicle.fitness_certificate_expiry.isoformat()}."
            )

        # 2. Compliance check: driver
        if driver.status != DriverStatus.ACTIVE.value:
            raise ConflictException(
                f"Driver {driver.full_name} status is {driver.status}."
            )
        if driver.license_expiry < payload.trip_date:
            raise ConflictException(
                f"Driver license expired on {driver.license_expiry.isoformat()}."
            )

        # 3. Conflict detection: Vehicle overlapping trip
        veh_conflict = await db.scalar(
            select(TransportTrip).where(
                TransportTrip.tenant_id == tenant_id,
                TransportTrip.vehicle_id == payload.vehicle_id,
                TransportTrip.trip_date == payload.trip_date,
                TransportTrip.service_window == payload.service_window.value
                if hasattr(payload.service_window, "value")
                else str(payload.service_window),
                TransportTrip.status.in_(
                    [
                        TripStatus.SCHEDULED.value,
                        TripStatus.READY.value,
                        TripStatus.DEPARTED.value,
                        TripStatus.IN_PROGRESS.value,
                    ]
                ),
            )
        )
        if veh_conflict:
            raise ConflictException(
                f"Vehicle {vehicle.registration_number} is already scheduled for Trip {veh_conflict.trip_number} during this service window."
            )

        # 4. Conflict detection: Driver overlapping trip
        drv_conflict = await db.scalar(
            select(TransportTrip).where(
                TransportTrip.tenant_id == tenant_id,
                TransportTrip.driver_id == payload.driver_id,
                TransportTrip.trip_date == payload.trip_date,
                TransportTrip.service_window == payload.service_window.value
                if hasattr(payload.service_window, "value")
                else str(payload.service_window),
                TransportTrip.status.in_(
                    [
                        TripStatus.SCHEDULED.value,
                        TripStatus.READY.value,
                        TripStatus.DEPARTED.value,
                        TripStatus.IN_PROGRESS.value,
                    ]
                ),
            )
        )
        if drv_conflict:
            raise ConflictException(
                f"Driver {driver.full_name} is already assigned to Trip {drv_conflict.trip_number} during this service window."
            )

        trip_count = (
            await db.scalar(
                select(func.count(TransportTrip.id)).where(
                    TransportTrip.tenant_id == tenant_id
                )
            )
            or 0
        )
        trip_num = f"TRIP-{payload.trip_date.strftime('%Y%m%d')}-{trip_count + 1:04d}"

        trip = TransportTrip(
            tenant_id=tenant_id,
            trip_number=trip_num,
            route_id=payload.route_id,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            trip_date=payload.trip_date,
            service_window=payload.service_window.value
            if hasattr(payload.service_window, "value")
            else str(payload.service_window),
            scheduled_start_time=payload.scheduled_start_time,
            scheduled_end_time=payload.scheduled_end_time,
            status=TripStatus.SCHEDULED.value,
            pre_trip_checklist_completed=payload.pre_trip_checklist_completed,
            checklist_notes=payload.checklist_notes,
        )
        db.add(trip)
        await db.flush()

        # Generate passenger manifest from active allocations on this route
        allocations = (
            await db.execute(
                select(TransportAllocation).where(
                    TransportAllocation.tenant_id == tenant_id,
                    TransportAllocation.route_id == payload.route_id,
                    TransportAllocation.status
                    == TransportAllocationStatus.ACTIVE.value,
                )
            )
        ).scalars().all()

        for alloc in allocations:
            manifest_entry = TransportBoardingRecord(
                tenant_id=tenant_id,
                trip_id=trip.id,
                student_id=alloc.student_id,
                allocation_id=alloc.id,
                stop_id=alloc.stop_id,
                boarding_status=BoardingStatus.EXPECTED.value,
                verification_method=VerificationMethod.MANUAL.value,
            )
            db.add(manifest_entry)

        await db.commit()
        await db.refresh(trip)
        return trip

    @staticmethod
    async def get_trip(
        db: AsyncSession, tenant_id: UUID, trip_id: UUID
    ) -> TransportTrip:
        trip = await db.scalar(
            select(TransportTrip)
            .options(
                selectinload(TransportTrip.route),
                selectinload(TransportTrip.vehicle),
                selectinload(TransportTrip.driver),
                selectinload(TransportTrip.boarding_records),
            )
            .where(TransportTrip.tenant_id == tenant_id, TransportTrip.id == trip_id)
        )
        if not trip:
            raise NotFoundException("Transport trip record not found.")
        return trip

    @staticmethod
    async def dispatch_trip(
        db: AsyncSession,
        tenant_id: UUID,
        trip_id: UUID,
        payload: TransportTripDispatch,
        dispatcher_id: UUID,
    ) -> TransportTrip:
        trip = await TransportService.get_trip(db, tenant_id, trip_id)
        if trip.status in [TripStatus.COMPLETED.value, TripStatus.CANCELLED.value]:
            raise ConflictException(
                f"Cannot dispatch trip in '{trip.status}' state."
            )

        # Substitute vehicle handling
        if payload.substitute_vehicle_id:
            sub_veh = await TransportService.get_vehicle(
                db, tenant_id, payload.substitute_vehicle_id
            )
            if sub_veh.status != VehicleStatus.ACTIVE.value:
                raise ConflictException(
                    f"Substitute vehicle {sub_veh.registration_number} is not active ({sub_veh.status})."
                )
            trip.vehicle_id = payload.substitute_vehicle_id

        # Substitute driver handling
        if payload.substitute_driver_id:
            sub_drv = await TransportService.get_driver(
                db, tenant_id, payload.substitute_driver_id
            )
            if sub_drv.status != DriverStatus.ACTIVE.value:
                raise ConflictException(
                    f"Substitute driver {sub_drv.full_name} is not active ({sub_drv.status})."
                )
            trip.driver_id = payload.substitute_driver_id

        trip.status = TripStatus.IN_PROGRESS.value
        trip.actual_start_time = payload.actual_start_time or datetime.now(
            UTC
        )
        if payload.start_odometer_km is not None:
            trip.start_odometer_km = payload.start_odometer_km
        trip.pre_trip_checklist_completed = payload.pre_trip_checklist_completed
        if payload.checklist_notes:
            trip.checklist_notes = payload.checklist_notes
        trip.dispatched_by_id = dispatcher_id

        await db.commit()
        await db.refresh(trip)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_TRIP_DISPATCHED,
            aggregate_type="TransportTrip",
            aggregate_id=trip.id,
            payload={
                "trip_id": str(trip.id),
                "route_id": str(trip.route_id),
                "vehicle_id": str(trip.vehicle_id),
                "driver_id": str(trip.driver_id),
                "trip_date": trip.trip_date.isoformat(),
                "service_window": trip.service_window,
            },
        )
        return trip

    @staticmethod
    async def complete_trip(
        db: AsyncSession,
        tenant_id: UUID,
        trip_id: UUID,
        end_odometer_km: Decimal | None = None,
        actual_end_time: datetime | None = None,
    ) -> TransportTrip:
        trip = await TransportService.get_trip(db, tenant_id, trip_id)
        trip.status = TripStatus.COMPLETED.value
        trip.actual_end_time = actual_end_time or datetime.now(UTC)
        if end_odometer_km is not None:
            if (
                trip.start_odometer_km
                and end_odometer_km < trip.start_odometer_km
            ):
                raise BadRequestException(
                    f"End odometer ({end_odometer_km}) cannot be less than start odometer ({trip.start_odometer_km})."
                )
            trip.end_odometer_km = end_odometer_km

            # Update vehicle odometer
            vehicle = await db.scalar(
                select(TransportVehicle).where(
                    TransportVehicle.tenant_id == tenant_id,
                    TransportVehicle.id == trip.vehicle_id,
                )
            )
            if vehicle and end_odometer_km > vehicle.current_odometer_km:
                vehicle.current_odometer_km = end_odometer_km

        await db.commit()
        await db.refresh(trip)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_TRIP_COMPLETED,
            aggregate_type="TransportTrip",
            aggregate_id=trip.id,
            payload={
                "trip_id": str(trip.id),
                "route_id": str(trip.route_id),
                "actual_end_time": trip.actual_end_time.isoformat(),
                "end_odometer_km": str(trip.end_odometer_km)
                if trip.end_odometer_km
                else "",
            },
        )
        return trip

    @staticmethod
    async def list_trips(
        db: AsyncSession,
        tenant_id: UUID,
        trip_date: date | None = None,
        route_id: UUID | None = None,
        status: str | None = None,
    ) -> list[TransportTrip]:
        stmt = (
            select(TransportTrip)
            .options(
                selectinload(TransportTrip.route),
                selectinload(TransportTrip.vehicle),
                selectinload(TransportTrip.driver),
            )
            .where(TransportTrip.tenant_id == tenant_id)
        )
        if trip_date:
            stmt = stmt.where(TransportTrip.trip_date == trip_date)
        if route_id:
            stmt = stmt.where(TransportTrip.route_id == route_id)
        if status and status != "ALL":
            stmt = stmt.where(TransportTrip.status == status)
        stmt = stmt.order_by(TransportTrip.scheduled_start_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 8. PASSENGER BOARDING & MANIFEST RECONCILIATION
    # =========================================================================

    @staticmethod
    async def record_boarding(
        db: AsyncSession,
        tenant_id: UUID,
        trip_id: UUID,
        payload: TransportBoardingVerifyRequest,
        verifier_id: UUID,
    ) -> TransportBoardingRecord:
        trip = await TransportService.get_trip(db, tenant_id, trip_id)

        record = await db.scalar(
            select(TransportBoardingRecord).where(
                TransportBoardingRecord.tenant_id == tenant_id,
                TransportBoardingRecord.trip_id == trip_id,
                TransportBoardingRecord.student_id == payload.student_id,
            )
        )
        if not record:
            # Unexpected passenger boarding
            record = TransportBoardingRecord(
                tenant_id=tenant_id,
                trip_id=trip_id,
                student_id=payload.student_id,
                stop_id=payload.stop_id,
                boarding_status=payload.boarding_status.value
                if hasattr(payload.boarding_status, "value")
                else str(payload.boarding_status),
                boarding_time=datetime.now(UTC),
                verification_method=payload.verification_method.value
                if hasattr(payload.verification_method, "value")
                else str(payload.verification_method),
                verified_by_user_id=verifier_id,
                remarks="Unregistered manifest boarding verified by attendant",
            )
            db.add(record)
        else:
            status_val = (
                payload.boarding_status.value
                if hasattr(payload.boarding_status, "value")
                else str(payload.boarding_status)
            )
            record.boarding_status = status_val
            record.verification_method = (
                payload.verification_method.value
                if hasattr(payload.verification_method, "value")
                else str(payload.verification_method)
            )
            record.verified_by_user_id = verifier_id
            if status_val == BoardingStatus.BOARDED.value:
                record.boarding_time = datetime.now(UTC)
            elif status_val == BoardingStatus.DROPPED_OFF.value:
                record.drop_off_time = datetime.now(UTC)

        await db.commit()
        await db.refresh(record)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_BOARDING_RECORDED,
            aggregate_type="TransportBoardingRecord",
            aggregate_id=record.id,
            payload={
                "record_id": str(record.id),
                "trip_id": str(record.trip_id),
                "student_id": str(record.student_id),
                "stop_id": str(record.stop_id),
                "boarding_status": record.boarding_status,
                "verification_method": record.verification_method,
            },
        )
        return record

    @staticmethod
    async def get_trip_manifest(
        db: AsyncSession, tenant_id: UUID, trip_id: UUID
    ) -> TripManifestResponse:
        trip = await TransportService.get_trip(db, tenant_id, trip_id)
        records = (
            await db.execute(
                select(TransportBoardingRecord)
                .where(
                    TransportBoardingRecord.tenant_id == tenant_id,
                    TransportBoardingRecord.trip_id == trip_id,
                )
                .order_by(TransportBoardingRecord.created_at.asc())
            )
        ).scalars().all()

        total = len(records)
        boarded = sum(
            1
            for r in records
            if r.boarding_status
            in [BoardingStatus.BOARDED.value, BoardingStatus.DROPPED_OFF.value]
        )
        absent = sum(
            1
            for r in records
            if r.boarding_status
            in [BoardingStatus.ABSENT.value, BoardingStatus.MISSED.value]
        )
        pending = total - boarded - absent

        return TripManifestResponse(
            trip=TransportTripResponse.model_validate(trip),
            total_manifest_count=total,
            boarded_count=boarded,
            absent_count=absent,
            pending_count=pending,
            passengers=[
                TransportBoardingRecordResponse.model_validate(r) for r in records
            ],
        )

    # =========================================================================
    # 9. TELEMATICS & TRUTHFUL LIVE TRACKING BOUNDARY
    # =========================================================================

    @staticmethod
    async def configure_tracking_source(
        db: AsyncSession,
        tenant_id: UUID,
        vehicle_id: UUID,
        payload: TransportTrackingSourceConfig,
    ) -> TransportTrackingSource:
        await TransportService.get_vehicle(db, tenant_id, vehicle_id)
        source = await db.scalar(
            select(TransportTrackingSource).where(
                TransportTrackingSource.tenant_id == tenant_id,
                TransportTrackingSource.vehicle_id == vehicle_id,
            )
        )
        if not source:
            source = TransportTrackingSource(
                tenant_id=tenant_id,
                vehicle_id=vehicle_id,
                provider_name=payload.provider_name,
                device_identifier=payload.device_identifier,
                is_enabled=payload.is_enabled,
                status=TrackingProviderStatus.ACTIVE.value
                if payload.is_enabled
                else TrackingProviderStatus.NOT_CONFIGURED.value,
            )
            db.add(source)
        else:
            source.provider_name = payload.provider_name
            source.device_identifier = payload.device_identifier
            source.is_enabled = payload.is_enabled
            source.status = (
                TrackingProviderStatus.ACTIVE.value
                if payload.is_enabled
                else TrackingProviderStatus.NOT_CONFIGURED.value
            )

        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def record_location_ping(
        db: AsyncSession, tenant_id: UUID, payload: TransportLocationPingRequest
    ) -> TransportLocationSnapshot:
        await TransportService.get_vehicle(db, tenant_id, payload.vehicle_id)

        snapshot = TransportLocationSnapshot(
            tenant_id=tenant_id,
            vehicle_id=payload.vehicle_id,
            trip_id=payload.trip_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            speed_kmh=payload.speed_kmh,
            heading_degrees=payload.heading_degrees,
            odometer_reading=payload.odometer_reading,
            recorded_at=payload.recorded_at,
            received_at=datetime.now(UTC),
            data_source=payload.data_source,
        )
        db.add(snapshot)

        # Update tracking source heartbeat
        source = await db.scalar(
            select(TransportTrackingSource).where(
                TransportTrackingSource.tenant_id == tenant_id,
                TransportTrackingSource.vehicle_id == payload.vehicle_id,
            )
        )
        if source:
            source.last_heartbeat_at = datetime.now(UTC)
            source.status = TrackingProviderStatus.ACTIVE.value

        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    @staticmethod
    async def get_live_tracking(
        db: AsyncSession, tenant_id: UUID, vehicle_id: UUID
    ) -> TransportLiveTrackingResponse:
        vehicle = await TransportService.get_vehicle(db, tenant_id, vehicle_id)
        source = await db.scalar(
            select(TransportTrackingSource).where(
                TransportTrackingSource.tenant_id == tenant_id,
                TransportTrackingSource.vehicle_id == vehicle_id,
            )
        )

        if not source or not source.is_enabled:
            return TransportLiveTrackingResponse(
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                tracking_enabled=False,
                status=TrackingProviderStatus.NOT_CONFIGURED,
                last_known_location=None,
                is_data_stale=True,
                freshness_seconds=None,
                telemetry_message="No tracking provider is configured for this vehicle.",
            )

        latest_snap = await db.scalar(
            select(TransportLocationSnapshot)
            .where(
                TransportLocationSnapshot.tenant_id == tenant_id,
                TransportLocationSnapshot.vehicle_id == vehicle_id,
            )
            .order_by(TransportLocationSnapshot.recorded_at.desc())
        )

        if not latest_snap:
            return TransportLiveTrackingResponse(
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                tracking_enabled=True,
                status=TrackingProviderStatus.OFFLINE,
                last_known_location=None,
                is_data_stale=True,
                freshness_seconds=None,
                telemetry_message="Telematics enabled, but no GPS snapshots have been received yet.",
            )

        now = datetime.now(UTC)
        rec_time = latest_snap.recorded_at
        if rec_time.tzinfo is None:
            rec_time = rec_time.replace(tzinfo=UTC)

        freshness_secs = int((now - rec_time).total_seconds())
        is_stale = freshness_secs > 300  # Stale if older than 5 minutes

        return TransportLiveTrackingResponse(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            tracking_enabled=True,
            status=TrackingProviderStatus.ACTIVE
            if not is_stale
            else TrackingProviderStatus.OFFLINE,
            last_known_location={
                "latitude": float(latest_snap.latitude),
                "longitude": float(latest_snap.longitude),
                "speed_kmh": float(latest_snap.speed_kmh),
                "heading_degrees": float(latest_snap.heading_degrees or 0.0),
                "recorded_at": latest_snap.recorded_at.isoformat(),
            },
            is_data_stale=is_stale,
            freshness_seconds=freshness_secs,
            telemetry_message="Live GPS telemetry feed active."
            if not is_stale
            else f"Telemetry feed stale. Last fix received {freshness_secs} seconds ago.",
        )

    # =========================================================================
    # 10. TRANSPORT FEES & FINANCE INVOICING
    # =========================================================================

    @staticmethod
    async def create_fee_plan(
        db: AsyncSession, tenant_id: UUID, payload: TransportFeePlanCreate
    ) -> TransportFeePlan:
        code = payload.code.strip().upper()
        existing = await db.scalar(
            select(TransportFeePlan).where(
                TransportFeePlan.tenant_id == tenant_id,
                TransportFeePlan.code == code,
            )
        )
        if existing:
            raise ConflictException(f"Transport fee plan code '{code}' already exists.")

        plan = TransportFeePlan(
            tenant_id=tenant_id,
            code=code,
            name=payload.name.strip(),
            academic_year_id=payload.academic_year_id,
            campus_id=payload.campus_id,
            route_id=payload.route_id,
            stop_id=payload.stop_id,
            service_type=payload.service_type.value
            if hasattr(payload.service_type, "value")
            else str(payload.service_type),
            amount=payload.amount,
            currency=payload.currency,
            billing_cycle=payload.billing_cycle.value
            if hasattr(payload.billing_cycle, "value")
            else str(payload.billing_cycle),
            is_active=payload.is_active,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def list_fee_plans(
        db: AsyncSession, tenant_id: UUID, is_active: bool | None = None
    ) -> list[TransportFeePlan]:
        stmt = select(TransportFeePlan).where(TransportFeePlan.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(TransportFeePlan.is_active == is_active)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def generate_transport_invoices(
        db: AsyncSession,
        tenant_id: UUID,
        payload: GenerateTransportInvoiceRequest,
        generated_by: UUID,
    ) -> GenerateTransportInvoiceResponse:
        stmt = select(TransportAllocation).where(
            TransportAllocation.tenant_id == tenant_id,
            TransportAllocation.status == TransportAllocationStatus.ACTIVE.value,
        )
        if payload.allocation_ids:
            stmt = stmt.where(TransportAllocation.id.in_(payload.allocation_ids))
        if payload.route_id:
            stmt = stmt.where(TransportAllocation.route_id == payload.route_id)

        allocations = (await db.execute(stmt)).scalars().all()
        created_invoice_ids: list[UUID] = []
        skipped = 0
        total_billed = Decimal("0.00")

        today = date.today()
        due_date = today + timedelta(days=payload.due_days)

        fee_cat = await db.scalar(
            select(FeeCategory).where(
                FeeCategory.tenant_id == tenant_id,
                FeeCategory.code == "TRANSPORT",
            )
        )
        if not fee_cat:
            fee_cat = FeeCategory(
                tenant_id=tenant_id,
                code="TRANSPORT",
                name="Transport Fee",
                description="Institutional Transport Service and Transit Passes",
                is_refundable=False,
                is_active=True,
            )
            db.add(fee_cat)
            await db.flush()

        for alloc in allocations:
            # Prevent duplicate invoices
            if alloc.finance_invoice_id:
                skipped += 1
                continue

            # Look up stop fare or route fee plan
            stop = await db.scalar(
                select(TransportStop).where(TransportStop.id == alloc.stop_id)
            )
            bill_amount = stop.fare_annual if stop and stop.fare_annual > 0 else Decimal("12000.00")

            inv_count = (
                await db.scalar(
                    select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
                )
                or 0
            )
            inv_num = f"INV-TR-{today.year}-{inv_count + 1:06d}"

            invoice = Invoice(
                tenant_id=tenant_id,
                student_id=alloc.student_id,
                academic_year_id=alloc.academic_year_id,
                invoice_number=inv_num,
                issue_date=today,
                due_date=due_date,
                currency="INR",
                gross_amount=bill_amount,
                concession_amount=Decimal("0.00"),
                adjustment_amount=Decimal("0.00"),
                net_payable=bill_amount,
                paid_amount=Decimal("0.00"),
                balance_amount=bill_amount,
                status="ISSUED",
                remarks=f"Transport Fee for Pass {alloc.pass_number}",
            )
            db.add(invoice)
            await db.flush()

            line_item = InvoiceLineItem(
                invoice_id=invoice.id,
                category_id=fee_cat.id,
                description=f"Institutional Transport Fee ({alloc.service_type})",
                amount=bill_amount,
            )
            db.add(line_item)

            alloc.finance_invoice_id = invoice.id
            alloc.fee_status = TransportFeeStatus.INVOICED.value
            created_invoice_ids.append(invoice.id)
            total_billed += bill_amount

        await db.commit()
        return GenerateTransportInvoiceResponse(
            invoices_created=len(created_invoice_ids),
            invoice_ids=created_invoice_ids,
            skipped_count=skipped,
            total_billed_amount=total_billed,
        )

    # =========================================================================
    # 11. FLEET MAINTENANCE & DEFECT REPORTING INTEGRATION
    # =========================================================================

    @staticmethod
    async def report_vehicle_defect(
        db: AsyncSession,
        tenant_id: UUID,
        vehicle_id: UUID,
        defect_description: str,
        reporter_id: UUID,
    ) -> MaintenanceWorkOrder:
        vehicle = await TransportService.get_vehicle(db, tenant_id, vehicle_id)
        vehicle.status = VehicleStatus.MAINTENANCE.value

        wo_count = (
            await db.scalar(
                select(func.count(MaintenanceWorkOrder.id)).where(
                    MaintenanceWorkOrder.tenant_id == tenant_id
                )
            )
            or 0
        )
        wo_number = f"WO-FLT-{date.today().year}-{wo_count + 1:04d}"

        work_order = MaintenanceWorkOrder(
            tenant_id=tenant_id,
            work_order_number=wo_number,
            asset_id=vehicle.asset_id or uuid.uuid4(),
            reported_by_id=reporter_id,
            reported_symptoms=f"Vehicle {vehicle.registration_number} Defect: {defect_description}",
            priority=MaintenancePriority.HIGH.value,
            severity=MaintenanceSeverity.CRITICAL.value,
            operational_impact=MaintenanceOperationalImpact.FULL_OUTAGE.value,
            status=MaintenanceOrderStatus.REPORTED.value,
        )
        db.add(work_order)
        await db.commit()
        await db.refresh(work_order)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_VEHICLE_MAINTENANCE_REQUIRED,
            aggregate_type="TransportVehicle",
            aggregate_id=vehicle.id,
            payload={
                "vehicle_id": str(vehicle.id),
                "registration_number": vehicle.registration_number,
                "defect_notes": defect_description,
                "work_order_id": str(work_order.id),
            },
        )
        return work_order

    # =========================================================================
    # 12. FUEL & OPERATING EXPENSES
    # =========================================================================

    @staticmethod
    async def create_fuel_log(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TransportFuelLogCreate,
        logged_by_id: UUID | None = None,
    ) -> TransportFuelLog:
        vehicle = await TransportService.get_vehicle(db, tenant_id, payload.vehicle_id)

        # Validate odometer progression
        if payload.odometer_reading < vehicle.current_odometer_km:
            raise BadRequestException(
                f"Fuel log odometer reading ({payload.odometer_reading}) cannot be less than vehicle's current recorded odometer ({vehicle.current_odometer_km})."
            )

        log = TransportFuelLog(
            tenant_id=tenant_id,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            trip_id=payload.trip_id,
            fuel_date=payload.fuel_date,
            odometer_reading=payload.odometer_reading,
            fuel_quantity_liters=payload.fuel_quantity_liters,
            fuel_cost_total=payload.fuel_cost_total,
            fuel_station_name=payload.fuel_station_name,
            receipt_number=payload.receipt_number,
            verified_by_id=logged_by_id,
            notes=payload.notes,
        )
        db.add(log)
        vehicle.current_odometer_km = payload.odometer_reading

        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def list_fuel_logs(
        db: AsyncSession,
        tenant_id: UUID,
        vehicle_id: UUID | None = None,
        driver_id: UUID | None = None,
    ) -> list[TransportFuelLog]:
        stmt = select(TransportFuelLog).where(TransportFuelLog.tenant_id == tenant_id)
        if vehicle_id:
            stmt = stmt.where(TransportFuelLog.vehicle_id == vehicle_id)
        if driver_id:
            stmt = stmt.where(TransportFuelLog.driver_id == driver_id)
        stmt = stmt.order_by(TransportFuelLog.fuel_date.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 13. INCIDENT MANAGEMENT
    # =========================================================================

    @staticmethod
    async def report_incident(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TransportIncidentCreate,
        reporter_id: UUID | None = None,
    ) -> TransportIncident:
        count = (
            await db.scalar(
                select(func.count(TransportIncident.id)).where(
                    TransportIncident.tenant_id == tenant_id
                )
            )
            or 0
        )
        inc_num = f"INC-TR-{date.today().year}-{count + 1:04d}"

        incident = TransportIncident(
            tenant_id=tenant_id,
            incident_number=inc_num,
            trip_id=payload.trip_id,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            route_id=payload.route_id,
            incident_type=payload.incident_type.value
            if hasattr(payload.incident_type, "value")
            else str(payload.incident_type),
            severity=payload.severity.value
            if hasattr(payload.severity, "value")
            else str(payload.severity),
            incident_time=payload.incident_time,
            location_description=payload.location_description.strip(),
            reporter_user_id=reporter_id,
            description=payload.description.strip(),
            action_taken=payload.action_taken,
            involved_student_ids=payload.involved_student_ids,
            emergency_services_contacted=payload.emergency_services_contacted,
            status=IncidentStatus.REPORTED.value,
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.TRANSPORT_INCIDENT_REPORTED,
            aggregate_type="TransportIncident",
            aggregate_id=incident.id,
            payload={
                "incident_id": str(incident.id),
                "incident_number": incident.incident_number,
                "trip_id": str(incident.trip_id) if incident.trip_id else "",
                "severity": incident.severity,
                "incident_type": incident.incident_type,
            },
        )
        return incident

    @staticmethod
    async def update_incident(
        db: AsyncSession,
        tenant_id: UUID,
        incident_id: UUID,
        payload: TransportIncidentUpdate,
    ) -> TransportIncident:
        incident = await db.scalar(
            select(TransportIncident).where(
                TransportIncident.tenant_id == tenant_id,
                TransportIncident.id == incident_id,
            )
        )
        if not incident:
            raise NotFoundException("Transport incident record not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(value, "value"):
                setattr(incident, key, value.value)
            else:
                setattr(incident, key, value)

        if (
            payload.status
            in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
            and not incident.resolved_at
        ):
            incident.resolved_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        tenant_id: UUID,
        severity: str | None = None,
        status: str | None = None,
    ) -> list[TransportIncident]:
        stmt = select(TransportIncident).where(TransportIncident.tenant_id == tenant_id)
        if severity and severity != "ALL":
            stmt = stmt.where(TransportIncident.severity == severity)
        if status and status != "ALL":
            stmt = stmt.where(TransportIncident.status == status)
        stmt = stmt.order_by(TransportIncident.incident_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 14. DASHBOARD & OPERATIONAL REPORTING
    # =========================================================================

    @staticmethod
    async def get_transport_dashboard(
        db: AsyncSession, tenant_id: UUID, campus_id: UUID | None = None
    ) -> TransportDashboardResponse:
        # Routes
        route_stmt = select(TransportRoute).where(TransportRoute.tenant_id == tenant_id)
        if campus_id:
            route_stmt = route_stmt.where(TransportRoute.campus_id == campus_id)
        routes = (await db.execute(route_stmt)).scalars().all()
        active_routes = sum(
            1 for r in routes if r.status == RouteStatus.ACTIVE.value
        )
        total_capacity = sum(r.capacity for r in routes if r.status == RouteStatus.ACTIVE.value)
        total_allocated_students = sum(
            r.allocated_students for r in routes if r.status == RouteStatus.ACTIVE.value
        )
        avg_utilization = (
            round((total_allocated_students / total_capacity * 100), 1)
            if total_capacity > 0
            else 0.0
        )

        # Stops
        total_stops = (
            await db.scalar(
                select(func.count(TransportStop.id)).join(
                    TransportRoute, TransportStop.route_id == TransportRoute.id
                ).where(TransportRoute.tenant_id == tenant_id)
            )
            or 0
        )

        # Vehicles
        veh_stmt = select(TransportVehicle).where(TransportVehicle.tenant_id == tenant_id)
        if campus_id:
            veh_stmt = veh_stmt.where(TransportVehicle.campus_id == campus_id)
        vehicles = (await db.execute(veh_stmt)).scalars().all()
        active_veh = sum(
            1 for v in vehicles if v.status == VehicleStatus.ACTIVE.value
        )
        maint_veh = sum(
            1 for v in vehicles if v.status == VehicleStatus.MAINTENANCE.value
        )

        # Drivers
        drivers = (
            await db.execute(
                select(TransportDriver).where(TransportDriver.tenant_id == tenant_id)
            )
        ).scalars().all()
        active_drv = sum(
            1 for d in drivers if d.status == DriverStatus.ACTIVE.value
        )

        # Allocations
        alloc_count = (
            await db.scalar(
                select(func.count(TransportAllocation.id)).where(
                    TransportAllocation.tenant_id == tenant_id,
                    TransportAllocation.status
                    == TransportAllocationStatus.ACTIVE.value,
                )
            )
            or 0
        )

        # Unassigned / Waitlisted
        unassigned_count = (
            await db.scalar(
                select(func.count(TransportApplication.id)).where(
                    TransportApplication.tenant_id == tenant_id,
                    TransportApplication.status.in_(
                        [
                            TransportApplicationStatus.SUBMITTED.value,
                            TransportApplicationStatus.WAITLISTED.value,
                        ]
                    ),
                )
            )
            or 0
        )

        # Upcoming vehicle compliance expiration within 30 days
        expiry_threshold = date.today() + timedelta(days=30)
        upcoming_maint = sum(
            1
            for v in vehicles
            if v.fitness_certificate_expiry <= expiry_threshold
            or v.insurance_expiry <= expiry_threshold
        )

        # Trips today
        today = date.today()
        trips_today = (
            await db.execute(
                select(TransportTrip).where(
                    TransportTrip.tenant_id == tenant_id,
                    TransportTrip.trip_date == today,
                )
            )
        ).scalars().all()
        active_trips_today = sum(
            1
            for t in trips_today
            if t.status
            in [TripStatus.IN_PROGRESS.value, TripStatus.DEPARTED.value]
        )
        completed_trips_today = sum(
            1 for t in trips_today if t.status == TripStatus.COMPLETED.value
        )

        # Incidents
        incidents_count = (
            await db.scalar(
                select(func.count(TransportIncident.id)).where(
                    TransportIncident.tenant_id == tenant_id,
                    TransportIncident.status != IncidentStatus.CLOSED.value,
                )
            )
            or 0
        )

        return TransportDashboardResponse(
            active_routes_count=active_routes,
            total_stops_count=total_stops,
            active_vehicles_count=active_veh,
            vehicles_under_maintenance_count=maint_veh,
            active_drivers_count=active_drv,
            students_allocated_count=alloc_count,
            route_capacity_utilization=avg_utilization,
            unassigned_students_count=unassigned_count,
            upcoming_vehicle_maintenance_count=upcoming_maint,
            active_trips_today=active_trips_today,
            completed_trips_today=completed_trips_today,
            incidents_reported_count=incidents_count,
        )

    @staticmethod
    async def get_route_utilization_report(
        db: AsyncSession, tenant_id: UUID
    ) -> list[RouteUtilizationReportItem]:
        routes = (
            await db.execute(
                select(TransportRoute)
                .options(
                    selectinload(TransportRoute.stops),
                    selectinload(TransportRoute.vehicle),
                    selectinload(TransportRoute.driver),
                )
                .where(TransportRoute.tenant_id == tenant_id)
            )
        ).scalars().all()

        report: list[RouteUtilizationReportItem] = []
        for r in routes:
            active_count = (
                await db.scalar(
                    select(func.count(TransportAllocation.id)).where(
                        TransportAllocation.tenant_id == tenant_id,
                        TransportAllocation.route_id == r.id,
                        TransportAllocation.status
                        == TransportAllocationStatus.ACTIVE.value,
                    )
                )
                or 0
            )
            pct = (
                round((active_count / r.capacity * 100), 1)
                if r.capacity > 0
                else 0.0
            )
            report.append(
                RouteUtilizationReportItem(
                    route_id=r.id,
                    route_code=r.route_code,
                    route_name=r.route_name,
                    capacity=r.capacity,
                    allocated_students=active_count,
                    utilization_percentage=pct,
                    stops_count=len(r.stops),
                    vehicle_registration=r.vehicle.registration_number
                    if r.vehicle
                    else None,
                    driver_name=r.driver.full_name if r.driver else None,
                )
            )
        return report

    # =========================================================================
    # 15. SCHEDULED OPERATIONS SWEEP
    # =========================================================================

    @staticmethod
    async def sweep_transport_operations(
        db: AsyncSession, tenant_id: UUID
    ) -> dict[str, int]:
        """Scheduled operations sweep for transport & fleet management (Step 55).

        Checks:
        1. Expiring vehicle fitness, insurance, and permits.
        2. Expiring driver licenses.
        3. Overdue in-progress trips.
        4. Expired waitlist offers.
        """
        metrics = {
            "expiring_vehicle_compliance": 0,
            "expiring_driver_licenses": 0,
            "overdue_in_progress_trips": 0,
            "expired_waitlist_offers": 0,
        }

        today = date.today()
        warn_date = today + timedelta(days=15)
        now = datetime.now(UTC)

        # 1. Vehicle compliance
        vehicles = (
            await db.execute(
                select(TransportVehicle).where(
                    TransportVehicle.tenant_id == tenant_id,
                    TransportVehicle.status == VehicleStatus.ACTIVE.value,
                    or_(
                        TransportVehicle.fitness_certificate_expiry <= warn_date,
                        TransportVehicle.insurance_expiry <= warn_date,
                    ),
                )
            )
        ).scalars().all()
        for v in vehicles:
            metrics["expiring_vehicle_compliance"] += 1
            await event_publisher.publish(
                db=db,
                tenant_id=tenant_id,
                event_type=DomainEventType.TRANSPORT_COMPLIANCE_EXPIRING,
                aggregate_type="TransportVehicle",
                aggregate_id=v.id,
                payload={
                    "vehicle_id": str(v.id),
                    "registration_number": v.registration_number,
                    "document_type": "FITNESS_OR_INSURANCE",
                    "expiry_date": v.fitness_certificate_expiry.isoformat(),
                },
            )

        # 2. Driver licenses
        drivers = (
            await db.execute(
                select(TransportDriver).where(
                    TransportDriver.tenant_id == tenant_id,
                    TransportDriver.status == DriverStatus.ACTIVE.value,
                    TransportDriver.license_expiry <= warn_date,
                )
            )
        ).scalars().all()
        for d in drivers:
            metrics["expiring_driver_licenses"] += 1

        # 3. Overdue trips
        overdue_trips = (
            await db.execute(
                select(TransportTrip).where(
                    TransportTrip.tenant_id == tenant_id,
                    TransportTrip.status.in_(
                        [TripStatus.IN_PROGRESS.value, TripStatus.DEPARTED.value]
                    ),
                    TransportTrip.scheduled_end_time < now - timedelta(hours=2),
                )
            )
        ).scalars().all()
        for trip in overdue_trips:
            metrics["overdue_in_progress_trips"] += 1

        # 4. Expired waitlist offers
        expired_wl = (
            await db.execute(
                select(TransportWaitlist).where(
                    TransportWaitlist.tenant_id == tenant_id,
                    TransportWaitlist.status == WaitlistStatus.OFFERED.value,
                    TransportWaitlist.expires_at < now,
                )
            )
        ).scalars().all()
        for wl in expired_wl:
            wl.status = WaitlistStatus.EXPIRED.value
            metrics["expired_waitlist_offers"] += 1

        await db.commit()
        return metrics
