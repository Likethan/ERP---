"""API Product Catalog, Operations & Changelog API Router (Step 21).

Enforces:
- Public and partner exploration of available API Products.
- Full inspection of classifications, deprecation schedules, and migration paths.
- Official API changelog access.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.platform_api.schemas import (
    ApiChangelogResponse,
    ApiOperationResponse,
    ApiProductResponse,
)
from app.platform_api.service import platform_service

router = APIRouter(prefix="/platform", tags=["API Platform - Catalog"])


@router.get("/catalog", response_model=list[ApiProductResponse])
async def list_api_catalog(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ApiProductResponse]:
    """Explore the CampusOS API Product catalog, classifications, and operations."""
    products = await platform_service.list_catalog(db)
    return [
        ApiProductResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            version=p.version,
            status=p.status,
            operations=[
                ApiOperationResponse(
                    id=op.id,
                    product_code=p.code,
                    method=op.method,
                    path=op.path,
                    version=op.version,
                    summary=op.summary,
                    description=op.description,
                    scope_required=op.scope_required,
                    classification=op.classification,
                    rate_limit_policy=op.rate_limit_policy,
                    governance_policy=op.governance_policy,
                    status=op.status,
                    deprecated_at=op.deprecated_at,
                    sunset_at=op.sunset_at,
                    replacement_path=op.replacement_path,
                    migration_notes=op.migration_notes,
                )
                for op in p.operations
            ],
        )
        for p in products
    ]


@router.get("/catalog/{product_code}", response_model=ApiProductResponse)
async def get_api_product(
    product_code: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiProductResponse:
    """Retrieve detailed operation specifications for a single API product."""
    product = await platform_service.get_catalog_product(db, product_code)
    return ApiProductResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        description=product.description,
        version=product.version,
        status=product.status,
        operations=[
            ApiOperationResponse(
                id=op.id,
                product_code=product.code,
                method=op.method,
                path=op.path,
                version=op.version,
                summary=op.summary,
                description=op.description,
                scope_required=op.scope_required,
                classification=op.classification,
                rate_limit_policy=op.rate_limit_policy,
                governance_policy=op.governance_policy,
                status=op.status,
                deprecated_at=op.deprecated_at,
                sunset_at=op.sunset_at,
                replacement_path=op.replacement_path,
                migration_notes=op.migration_notes,
            )
            for op in product.operations
        ],
    )


@router.get("/changelog", response_model=list[ApiChangelogResponse])
async def get_api_changelog(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ApiChangelogResponse]:
    """View official API version history, breaking changes, and migration advisories."""
    logs = await platform_service.list_changelogs(db)
    return [ApiChangelogResponse.model_validate(entry) for entry in logs]
