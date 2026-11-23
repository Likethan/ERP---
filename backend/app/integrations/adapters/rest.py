"""Generic REST Client Adapter."""

from typing import Any

from app.integrations.adapters.base import BaseIntegrationAdapter
from app.integrations.security import SafeHttpClient, SafeHttpResponse


class GenericRestAdapter(BaseIntegrationAdapter):
    """Adapter for interacting with arbitrary external REST APIs safely."""

    async def ping(self) -> bool:
        base_url = self.configuration.get("base_url")
        if not base_url:
            return True
        try:
            resp = await SafeHttpClient.request(
                method="GET",
                url=base_url,
                timeout_seconds=5.0,
                allowed_domains=self.connector.allowed_domains,
            )
            return resp.status_code < 400
        except Exception:
            return False

    async def execute_request(
        self,
        method: str,
        path: str = "",
        headers: dict[str, str] | None = None,
        json_data: Any = None,
        timeout_seconds: float = 10.0,
        allow_private_networks_for_tests: bool = False,
    ) -> SafeHttpResponse:
        """Send authenticated HTTP request to configured external base URL."""
        base_url = self.configuration.get("base_url", "").rstrip("/")
        full_url = f"{base_url}/{path.lstrip('/')}" if path else base_url

        req_headers = dict(headers or {})

        # Inject credentials safely based on auth type
        api_key = self.credentials.get("api_key")
        bearer_token = self.credentials.get("token") or self.credentials.get("access_token")
        if api_key:
            req_headers["X-API-Key"] = api_key
        elif bearer_token:
            req_headers["Authorization"] = f"Bearer {bearer_token}"

        return await SafeHttpClient.request(
            method=method,
            url=full_url,
            headers=req_headers,
            json_data=json_data,
            timeout_seconds=timeout_seconds,
            allowed_domains=self.connector.allowed_domains,
            allow_private_networks_for_tests=allow_private_networks_for_tests,
        )
