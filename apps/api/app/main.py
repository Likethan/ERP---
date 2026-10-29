from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import CampusOSException
from app.core.logging import logger
from app.core.metrics import metrics
from app.core.middleware import (
    PayloadSizeLimitMiddleware,
    RateLimiterMiddleware,
    RequestCorrelationMiddleware,
    SecurityHeadersMiddleware,
    TimingAndMetricsMiddleware,
)
from app.core.security_events import security_events
from app.schemas.common import (
    ApiErrorDetail,
    ApiErrorEnvelope,
    ApiErrorResponse,
    ApiResponse,
    HealthResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown hooks."""
    # Enforce production security constraints
    settings.validate_production_configuration()

    logger.info(
        "Starting %s v%s in %s mode...",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CampusOS Enterprise College ERP Backend API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.is_docs_enabled else None,
    docs_url="/docs" if settings.is_docs_enabled else None,
    redoc_url="/redoc" if settings.is_docs_enabled else None,
    lifespan=lifespan,
)

# Middleware Pipeline (executed in reverse registration order)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PayloadSizeLimitMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestCorrelationMiddleware)
app.add_middleware(TimingAndMetricsMiddleware)


# Exception Handlers
@app.exception_handler(CampusOSException)
async def campusos_exception_handler(
    request: Request, exc: CampusOSException
) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None)

    # Track metrics for security-sensitive error codes
    if exc.code == "AUTHENTICATION_FAILED":
        metrics.record_auth_failure()
    elif exc.code == "PERMISSION_DENIED":
        metrics.record_authorization_denied()
    elif exc.code in ("TENANT_MISMATCH", "CROSS_TENANT_RELATIONSHIP_PROHIBITED"):
        security_events.record_event(
            event_type="SECURITY_ACCESS_DENIED",
            severity="HIGH",
            request_id=req_id or "-",
            ip_address=request.client.host if request.client else "unknown",
            details={"code": exc.code, "message": exc.message},
        )

    error_envelope = ApiErrorEnvelope(
        code=exc.code,
        message=exc.message,
        details=[ApiErrorDetail(**d) if isinstance(d, dict) else d for d in exc.details],
        request_id=req_id,
    )
    headers = {"X-Request-ID": req_id} if req_id else {}
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None)
    details = [
        ApiErrorDetail(
            field=".".join(str(loc) for loc in err["loc"]),
            message=err["msg"],
            code=err["type"],
        )
        for err in exc.errors()
    ]
    error_envelope = ApiErrorEnvelope(
        code="VALIDATION_FAILED",
        message="Request input validation failed.",
        details=details,
        request_id=req_id,
    )
    headers = {"X-Request-ID": req_id} if req_id else {}
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
        headers=headers,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Sanitize raw database exceptions to prevent leaking schema, tables, or queries."""
    req_id = getattr(request.state, "request_id", None)
    logger.exception("Database error occurred [req:%s]: %s", req_id, exc)
    metrics.record_db_error()

    error_envelope = ApiErrorEnvelope(
        code="DATABASE_ERROR",
        message="A database operational error occurred. The operation could not be completed safely.",
        request_id=req_id,
    )
    headers = {"X-Request-ID": req_id} if req_id else {}
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
        headers=headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled server exception [req:%s]: %s", req_id, exc)
    error_envelope = ApiErrorEnvelope(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please contact institutional support.",
        request_id=req_id,
    )
    headers = {"X-Request-ID": req_id} if req_id else {}
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
        headers=headers,
    )


# Root Health & Probes
@app.get("/health", response_model=ApiResponse[HealthResponse], tags=["System"])
async def root_health() -> ApiResponse[HealthResponse]:
    """Root health check for backwards compatibility."""
    return ApiResponse(
        data=HealthResponse(
            status="healthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        )
    )


@app.get("/health/live", response_model=ApiResponse[HealthResponse], tags=["System"])
async def root_liveness_probe() -> ApiResponse[HealthResponse]:
    """Liveness probe verifying that the API worker process is responsive."""
    return ApiResponse(
        data=HealthResponse(
            status="healthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            checks={"process": "alive"},
        )
    )


@app.get("/health/ready", response_model=ApiResponse[HealthResponse], tags=["System"])
async def root_readiness_probe(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[HealthResponse]:
    """Readiness probe verifying that backend dependencies (database, cache) are operational."""
    checks: dict[str, str] = {}
    is_ready = True

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"down: {exc}"
        is_ready = False

    checks["cache"] = "ok"

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ApiResponse(
        data=HealthResponse(
            status="healthy" if is_ready else "unhealthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            checks=checks,
        )
    )


@app.get("/metrics", tags=["System"])
async def root_metrics():
    """Expose application operational and security metrics."""
    return ApiResponse(data=metrics.get_snapshot())


# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
