from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import CampusOSException
from app.core.logging import logger
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
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(CampusOSException)
async def campusos_exception_handler(
    request: Request, exc: CampusOSException
) -> JSONResponse:
    error_envelope = ApiErrorEnvelope(
        code=exc.code,
        message=exc.message,
        details=[ApiErrorDetail(**d) if isinstance(d, dict) else d for d in exc.details],
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
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
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    error_envelope = ApiErrorEnvelope(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please contact institutional support.",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiErrorResponse(error=error_envelope).model_dump(),
    )


# Root health probe
@app.get("/health", response_model=ApiResponse[HealthResponse], tags=["System"])
async def root_health() -> ApiResponse[HealthResponse]:
    return ApiResponse(
        data=HealthResponse(
            status="healthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        )
    )


# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
