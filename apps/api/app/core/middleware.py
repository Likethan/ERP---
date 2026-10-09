"""HTTP Security, Correlation, Size Limit, and Observability Middlewares for CampusOS."""

import time
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.logging import correlation_id_ctx
from app.core.metrics import metrics
from app.core.rate_limiter import rate_limiter
from app.schemas.common import ApiErrorDetail, ApiErrorEnvelope, ApiErrorResponse


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Ensures every HTTP request has a traceable, unique correlation/request ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        # Validate format or generate clean UUID4
        if incoming_id and len(incoming_id) <= 64 and incoming_id.replace("-", "").isalnum():
            request_id = incoming_id
        else:
            request_id = str(uuid4())

        request.state.request_id = request_id
        token = correlation_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            correlation_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects enterprise HTTP security headers across all API responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if settings.SECURITY_HEADERS_ENABLED:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

            if settings.HSTS_ENABLED or settings.ENVIRONMENT == "production":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            # Allow documentation assets if loading OpenAPI docs, otherwise strict CSP
            path = request.url.path
            if path in ("/docs", "/redoc", "/api/v1/openapi.json"):
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self' https://cdn.jsdelivr.net; "
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "img-src 'self' data: https://fastapi.tiangolo.com; "
                    "frame-ancestors 'none';"
                )
            else:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; frame-ancestors 'none';"
                )

        return response


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces strict upper bounds on incoming request payload sizes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length_header = request.headers.get("Content-Length")
        if content_length_header:
            try:
                content_length = int(content_length_header)
            except ValueError:
                content_length = 0

            # Determine limit based on content type (multipart upload vs JSON)
            content_type = request.headers.get("Content-Type", "")
            is_multipart = "multipart/form-data" in content_type
            max_limit = settings.MAX_MULTIPART_BYTES if is_multipart else settings.MAX_JSON_BODY_BYTES

            if content_length > max_limit:
                req_id = getattr(request.state, "request_id", str(uuid4()))
                envelope = ApiErrorEnvelope(
                    code="PAYLOAD_TOO_LARGE",
                    message=(
                        f"Request payload of {content_length} bytes exceeds the allowed limit "
                        f"of {max_limit} bytes."
                    ),
                    request_id=req_id,
                    details=[
                        ApiErrorDetail(
                            field="Content-Length",
                            message=f"Payload {content_length}B exceeds maximum {max_limit}B",
                            code="SIZE_EXCEEDED",
                        )
                    ],
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content=ApiErrorResponse(error=envelope).model_dump(),
                    headers={"X-Request-ID": req_id},
                )

        return await call_next(request)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Enforces route and client-specific rate limiting."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        # Exclude internal health and docs probes from rate limiting
        if path in ("/health", "/health/live", "/health/ready", "/docs", "/redoc", "/api/v1/openapi.json"):
            return await call_next(request)

        if not rate_limiter.enabled or not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        # Forwarded header support if behind proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        # In testing environments, bypass rate limiter unless explicitly enabled for a security test
        if client_ip in ("testclient", "testserver", "127.0.0.1") and settings.ENVIRONMENT != "production":
            if not getattr(rate_limiter, "enabled_for_tests", False) and request.headers.get("X-Enable-Rate-Limit") != "true":
                return await call_next(request)

        # Check rate limiter
        allowed, retry_after, category = rate_limiter.check_request(
            path=path,
            client_ip=client_ip,
        )


        if not allowed:
            req_id = getattr(request.state, "request_id", str(uuid4()))
            envelope = ApiErrorEnvelope(
                code="RATE_LIMIT_EXCEEDED",
                message=f"Too many requests to {category} endpoint. Please retry after {retry_after} seconds.",
                request_id=req_id,
                details=[
                    ApiErrorDetail(
                        field="rate_limit",
                        message=f"Retry after {retry_after}s",
                        code="THROTTLED",
                    )
                ],
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ApiErrorResponse(error=envelope).model_dump(),
                headers={
                    "Retry-After": str(retry_after),
                    "X-Request-ID": req_id,
                },
            )

        return await call_next(request)


class TimingAndMetricsMiddleware(BaseHTTPMiddleware):
    """Tracks latency and HTTP operational metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        # Record metrics
        metrics.record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=duration,
        )
        return response
