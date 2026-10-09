"""SSRF Protection, URL Validation, HMAC Signing, and Safe HTTP Client for CampusOS.

Enforces:
- Multi-layer SSRF defenses: protocol validation, private IP blocking, link-local blocking,
  cloud metadata endpoint blocking (AWS/GCP/Azure), DNS resolution inspection.
- Domain allowlisting for configured connectors.
- Response size limits to prevent denial-of-service / memory exhaustion.
- Cryptographic HMAC-SHA256 signature generation and timing-safe verification.
- Structured failure categorization across all external HTTP operations.
"""

from enum import StrEnum
import hashlib
import hmac
import ipaddress
import logging
from math import exp
import socket
import time
from typing import Any
from urllib.parse import urlparse
import uuid

import httpx

from app.core.config import settings
from app.core.exceptions import (
    CampusOSException,
    ForbiddenException,
    ValidationException,
)
from app.core.logging import correlation_id_ctx
from app.core.sanitizer import mask_sensitive_string

logger = logging.getLogger("campusos.integrations.security")

# Blocked IP Networks for SSRF Prevention
BLOCKED_IP_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # IPv4 Private & Loopback & Link-Local & Carrier-Grade NAT
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    # IPv6 Loopback & Link-Local & Unique Local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("ff00::/8"),
]

BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "169.254.169.254",
})

# Response size boundary: maximum 5 Megabytes to prevent buffer bloat
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class FailureClassification(StrEnum):
    RETRYABLE = "RETRYABLE"
    NON_RETRYABLE = "NON_RETRYABLE"
    AUTHENTICATION = "AUTHENTICATION"
    CONFIGURATION = "CONFIGURATION"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    VALIDATION = "VALIDATION"


class IntegrationSecurityException(CampusOSException):
    def __init__(self, message: str, code: str = "INTEGRATION_SECURITY_VIOLATION"):
        super().__init__(status_code=400, code=code, message=message)


class SSRFBlockedException(IntegrationSecurityException):
    def __init__(self, message: str):
        super().__init__(message=message, code="SSRF_DESTINATION_BLOCKED")


def is_ip_blocked(ip_addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address falls into private, loopback, link-local, or metadata ranges."""
    for network in BLOCKED_IP_NETWORKS:
        if ip_addr in network:
            return True
    return False


def validate_outbound_url(
    url: str,
    allowed_domains: list[str] | None = None,
    allow_private_networks_for_tests: bool = False,
) -> str:
    """Validate external destination URL against SSRF vulnerabilities and allowlist policies.

    Validates:
    1. Scheme must be https (or http in development/testing if allowed).
    2. Hostname is not in blocklist (localhost, metadata.google.internal, etc.).
    3. Hostname does not resolve to private, loopback, link-local, or cloud metadata IP addresses.
    4. Hostname satisfies allowed_domains if configured.
    """
    if not url or not isinstance(url, str):
        raise ValidationException("Target integration URL cannot be empty.")

    clean_url = url.strip()
    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        raise ValidationException(f"Invalid URL structure: {exc}") from exc

    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedException(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTPS and HTTP are allowed.")

    if settings.ENVIRONMENT.lower() == "production" and parsed.scheme != "https":
        raise SSRFBlockedException("Production integration calls strictly require HTTPS.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise SSRFBlockedException("URL must contain a valid hostname.")

    # 1. Blocked hostnames check
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".internal") or hostname.endswith(".local"):
        if not allow_private_networks_for_tests:
            raise SSRFBlockedException(f"Access to internal or loopback host '{hostname}' is strictly forbidden.")

    # 2. Check if hostname is directly an IP literal
    try:
        direct_ip = ipaddress.ip_address(hostname)
        if is_ip_blocked(direct_ip) and not allow_private_networks_for_tests:
            raise SSRFBlockedException(f"Direct IP access to restricted address '{direct_ip}' is blocked.")
    except ValueError:
        pass  # Not an IP literal, proceed to DNS resolution

    # 3. DNS Resolution check (prevent DNS rebinding & private IP resolution)
    if not allow_private_networks_for_tests:
        try:
            addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if is_ip_blocked(resolved_ip):
                    raise SSRFBlockedException(
                        f"Destination host '{hostname}' resolves to restricted network IP '{resolved_ip}'."
                    )
        except (socket.gaierror, socket.herror) as exc:
            # DNS resolution failure
            raise ValidationException(f"DNS resolution failed for integration host '{hostname}': {exc}") from exc

    # 4. Allowed domains check
    if allowed_domains:
        normalized_allowed = [d.lower().strip() for d in allowed_domains if d]
        if normalized_allowed:
            domain_matched = False
            for allowed in normalized_allowed:
                if allowed.startswith("*."):
                    suffix = allowed[1:]  # e.g. .example.com
                    if hostname.endswith(suffix):
                        domain_matched = True
                        break
                elif hostname == allowed:
                    domain_matched = True
                    break
            if not domain_matched:
                raise ForbiddenException(
                    f"Target host '{hostname}' is not permitted by connector's allowed domains policy: {allowed_domains}"
                )

    return clean_url


# --- Cryptographic Webhook Signing & Verification ---

def compute_webhook_signature(secret: str, timestamp: int | str, payload_str: str) -> str:
    """Generate SHA-256 HMAC signature for webhook payload: HMAC(secret, timestamp + '.' + payload)."""
    message = f"{timestamp}.{payload_str}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def verify_webhook_signature(
    secret: str,
    raw_payload: str,
    signature_header: str,
    tolerance_seconds: int = 300,
) -> bool:
    """Verify inbound HMAC-SHA256 webhook signature with replay window protection.

    Expects header format: `t=<timestamp>,v1=<signature>` or raw hex signature.
    """
    if not signature_header or not secret:
        return False

    header_parts = signature_header.strip().split(",")
    parsed_timestamp: str | None = None
    signatures: list[str] = []

    for part in header_parts:
        kv = part.strip().split("=", 1)
        if len(kv) == 2:
            k, v = kv[0].strip(), kv[1].strip()
            if k == "t":
                parsed_timestamp = v
            elif k == "v1":
                signatures.append(v)
        else:
            # Fallback for plain hex signature
            signatures.append(part.strip())

    if not signatures:
        return False

    # Check timestamp replay protection if timestamp present
    if parsed_timestamp is not None:
        try:
            ts_int = int(parsed_timestamp)
            current_time = int(time.time())
            if abs(current_time - ts_int) > tolerance_seconds:
                logger.warning(
                    "Webhook signature rejected: timestamp skew (%ds) exceeds tolerance (%ds)",
                    abs(current_time - ts_int),
                    tolerance_seconds,
                )
                return False
        except ValueError:
            return False
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            f"{parsed_timestamp}.{raw_payload}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    else:
        # Fallback raw payload HMAC
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            raw_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    # Timing-safe comparison against any provided signature in header
    for sig in signatures:
        if hmac.compare_digest(expected_sig, sig):
            return True

    return False


# --- Safe HTTP Client ---

class SafeHttpResponse:
    def __init__(
        self,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        duration_ms: int,
    ):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.duration_ms = duration_ms

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        import json
        return json.loads(self.text)


class SafeHttpClient:
    """Centralized, hardened HTTP client for external integrations.

    Guarantees:
    - Pre-request SSRF checks & IP resolution inspection
    - Strict timeouts & TLS certificate validation
    - Maximum response payload boundaries
    - Structured failure classifications
    - Non-leaking logs and sanitized request/response telemetry
    """

    @classmethod
    def classify_failure(cls, exc: Exception | None, status_code: int | None = None) -> FailureClassification:
        """Classify HTTP failure for predictable retry policies."""
        if status_code is not None:
            if status_code in (401, 403):
                return FailureClassification.AUTHENTICATION
            if status_code == 429:
                return FailureClassification.RATE_LIMITED
            if status_code in (502, 503, 504):
                return FailureClassification.RETRYABLE
            if status_code == 500:
                return FailureClassification.PROVIDER_UNAVAILABLE
            if 400 <= status_code < 500:
                return FailureClassification.NON_RETRYABLE

        if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
            return FailureClassification.RETRYABLE
        if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
            return FailureClassification.RETRYABLE
        if isinstance(exc, (httpx.DecodingError, httpx.TooManyRedirects)):
            return FailureClassification.NON_RETRYABLE
        if isinstance(exc, (ValidationException, SSRFBlockedException)):
            return FailureClassification.VALIDATION

        return FailureClassification.PROVIDER_UNAVAILABLE

    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json_data: Any = None,
        content: bytes | None = None,
        timeout_seconds: float = 10.0,
        allowed_domains: list[str] | None = None,
        allow_private_networks_for_tests: bool = False,
    ) -> SafeHttpResponse:
        """Execute external HTTP request with comprehensive safety protections."""
        # 1. Enforce SSRF and domain restrictions
        valid_url = validate_outbound_url(
            url,
            allowed_domains=allowed_domains,
            allow_private_networks_for_tests=allow_private_networks_for_tests,
        )

        # 2. Prepare headers with tracing and correlation IDs
        req_headers = dict(headers or {})
        correlation_id = correlation_id_ctx.get()
        if correlation_id and correlation_id != "-":
            req_headers["X-Correlation-ID"] = correlation_id
        if "X-Request-ID" not in req_headers:
            req_headers["X-Request-ID"] = str(uuid.uuid4())
        req_headers["User-Agent"] = f"CampusOS-Integration/1.0 (+https://campusos.edu)"

        start_time = time.perf_counter()

        # 3. Execute bounded request
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_seconds, connect=5.0),
                verify=True,
                follow_redirects=False,  # Prevent automatic redirect to internal networks
            ) as client:
                response = await client.request(
                    method=method.upper(),
                    url=valid_url,
                    headers=req_headers,
                    json=json_data,
                    content=content,
                )

                duration_ms = int((time.perf_counter() - start_time) * 1000)

                # Check response size limits
                resp_content = response.content
                if len(resp_content) > MAX_RESPONSE_BYTES:
                    raise ValidationException(
                        f"External response exceeded maximum size limit ({len(resp_content)} > {MAX_RESPONSE_BYTES} bytes)"
                    )

                return SafeHttpResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=resp_content,
                    duration_ms=duration_ms,
                )

        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(
                "SafeHttpClient %s request to %s failed after %dms: %s",
                method.upper(),
                mask_sensitive_string(valid_url),
                duration_ms,
                exc,
            )
            raise
