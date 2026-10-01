"""Academic structure endpoints: Regulations, Academic Years, Semesters, Batches, Sections."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    CORE_ACADEMIC_YEARS_MANAGE,
    CORE_ACADEMIC_YEARS_READ,
    CORE_PROGRAMS_MANAGE,
    CORE_PROGRAMS_READ,
    CORE_REGULATIONS_MANAGE,
    CORE_SECTIONS_MANAGE,
    CORE_SECTIONS_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import (
    AcademicYearCreateRequest,
    AcademicYearResponse,
    BatchCreateRequest,
    BatchResponse,
    RegulationCreateRequest,
    RegulationResponse,
    SectionCreateRequest,
    SectionResponse,
    SemesterCreateRequest,
    SemesterResponse,
)
from app.services.core_service import CoreService

router = APIRouter(tags=["Academic Structure"])


# --- Regulations ---
@router.get("/regulations", response_model=ApiResponse[list[RegulationResponse]])
async def list_regulations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[RegulationResponse]]:
    regulations = await CoreService.list_regulations(db, tenant.tenant_id)
    return ApiResponse(data=[RegulationResponse.model_validate(r) for r in regulations])


@router.post(
    "/regulations",
    response_model=ApiResponse[RegulationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_regulation(
    payload: RegulationCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_REGULATIONS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[RegulationResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    reg = await CoreService.create_regulation(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=RegulationResponse.model_validate(reg))


# --- Academic Years ---
@router.get("/academic-years", response_model=ApiResponse[list[AcademicYearResponse]])
async def list_academic_years(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_ACADEMIC_YEARS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AcademicYearResponse]]:
    years = await CoreService.list_academic_years(db, tenant.tenant_id)
    return ApiResponse(data=[AcademicYearResponse.model_validate(y) for y in years])


@router.post(
    "/academic-years",
    response_model=ApiResponse[AcademicYearResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_academic_year(
    payload: AcademicYearCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_ACADEMIC_YEARS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AcademicYearResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    ay = await CoreService.create_academic_year(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=AcademicYearResponse.model_validate(ay))


# --- Semesters ---
@router.get("/semesters", response_model=ApiResponse[list[SemesterResponse]])
async def list_semesters(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_ACADEMIC_YEARS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = Query(None),
) -> ApiResponse[list[SemesterResponse]]:
    semesters = await CoreService.list_semesters(
        db, tenant.tenant_id, academic_year_id=academic_year_id
    )
    return ApiResponse(data=[SemesterResponse.model_validate(s) for s in semesters])


@router.post(
    "/semesters",
    response_model=ApiResponse[SemesterResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_semester(
    payload: SemesterCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_ACADEMIC_YEARS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SemesterResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    sem = await CoreService.create_semester(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=SemesterResponse.model_validate(sem))


# --- Batches ---
@router.get("/batches", response_model=ApiResponse[list[BatchResponse]])
async def list_batches(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    program_id: UUID | None = Query(None),
) -> ApiResponse[list[BatchResponse]]:
    batches = await CoreService.list_batches(db, tenant.tenant_id, program_id=program_id)
    return ApiResponse(data=[BatchResponse.model_validate(b) for b in batches])


@router.post(
    "/batches",
    response_model=ApiResponse[BatchResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_batch(
    payload: BatchCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[BatchResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    batch = await CoreService.create_batch(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=BatchResponse.model_validate(batch))


# --- Sections ---
@router.get("/sections", response_model=ApiResponse[list[SectionResponse]])
async def list_sections(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_SECTIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    program_id: UUID | None = Query(None),
    batch_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
) -> ApiResponse[list[SectionResponse]]:
    sections = await CoreService.list_sections(
        db,
        tenant.tenant_id,
        program_id=program_id,
        batch_id=batch_id,
        semester_id=semester_id,
    )
    return ApiResponse(data=[SectionResponse.model_validate(s) for s in sections])


@router.post(
    "/sections",
    response_model=ApiResponse[SectionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_section(
    payload: SectionCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_SECTIONS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SectionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    section = await CoreService.create_section(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=SectionResponse.model_validate(section))
