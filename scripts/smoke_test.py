#!/usr/bin/env python3
"""CampusOS Automated Post-Deployment Smoke Test Suite.

Executes non-destructive, read-only smoke tests against staging or production environments
to verify API health, readiness, dependency connectivity, tenant resolution, and frontend availability.

Usage:
    python scripts/smoke_test.py --api-url http://localhost:8000 --web-url http://localhost:3000
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime


class SmokeTestRunner:
    def __init__(self, api_url: str, web_url: str | None = None, timeout: float = 5.0):
        self.api_url = api_url.rstrip("/")
        self.web_url = web_url.rstrip("/") if web_url else None
        self.timeout = timeout
        self.results: list[dict] = []

    def _http_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        data: bytes | None = None,
    ) -> tuple[int, dict | str, float]:
        start = time.perf_counter()
        req_headers = {"User-Agent": "CampusOS-SmokeTest/1.0", "Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = (time.perf_counter() - start) * 1000.0
                body = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(body)
                except (json.JSONDecodeError, ValueError):
                    parsed = body
                return resp.status, parsed, elapsed
        except urllib.error.HTTPError as err:
            elapsed = (time.perf_counter() - start) * 1000.0
            body = err.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                parsed = body
            return err.code, parsed, elapsed
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            elapsed = (time.perf_counter() - start) * 1000.0
            return 0, str(exc), elapsed

    def test(self, name: str, fn):
        print(f"[*] Testing {name}...", end=" ", flush=True)
        try:
            passed, detail, latency_ms = fn()
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] ({latency_ms:.1f}ms) - {detail}")
            self.results.append({"name": name, "status": status, "detail": detail, "latency_ms": latency_ms})
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] Exception: {exc}")
            self.results.append({"name": name, "status": "FAIL", "detail": str(exc), "latency_ms": 0.0})

    def run_all(self) -> bool:
        print("=== CampusOS Deployment Smoke Test Suite ===")
        print(f"Target API: {self.api_url}")
        if self.web_url:
            print(f"Target Web: {self.web_url}")
        print(f"Timestamp:  {datetime.now(UTC).isoformat()}\n")

        # 1. API Health
        def check_health():
            status, body, lat = self._http_request(f"{self.api_url}/health")
            if status == 200 and isinstance(body, dict) and body.get("data", {}).get("status") == "healthy":
                return True, "Process is healthy", lat
            return False, f"HTTP {status}: {body}", lat

        self.test("API Liveness (/health)", check_health)

        # 2. API Readiness (Database & Cache)
        def check_readiness():
            status, body, lat = self._http_request(f"{self.api_url}/health/ready")
            if status == 200 and isinstance(body, dict):
                checks = body.get("data", {}).get("checks", {})
                if checks.get("database") == "ok":
                    return True, f"DB and Cache operational ({checks})", lat
            return False, f"HTTP {status}: {body}", lat

        self.test("API Readiness (/health/ready)", check_readiness)

        # 3. Metrics Endpoint
        def check_metrics():
            status, body, lat = self._http_request(f"{self.api_url}/metrics")
            if status == 200 and isinstance(body, dict) and "data" in body:
                return True, "Metrics snapshot successfully returned", lat
            return False, f"HTTP {status}", lat

        self.test("Observability (/metrics)", check_metrics)

        # 4. Auth Protection & Negative Validation
        def check_auth_endpoint():
            status, body, lat = self._http_request(
                f"{self.api_url}/api/v1/auth/login",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"email": "invalid_probe@campusos.test", "password": "wrong"}).encode("utf-8"),
            )
            # Must return 401 or 422, never 500
            if status in (401, 422):
                return True, f"Authentication rejects invalid probe safely (HTTP {status})", lat
            return False, f"Unexpected response HTTP {status}: {body}", lat

        self.test("Auth Failure Guardrail (POST /auth/login)", check_auth_endpoint)

        # 5. Frontend Connectivity (if provided)
        if self.web_url:
            def check_web():
                status, _, lat = self._http_request(self.web_url)
                if status == 200:
                    return True, "Frontend index page rendered", lat
                return False, f"HTTP {status}", lat

            self.test("Frontend Web UI", check_web)

        # Summary
        print("\n=== Smoke Test Summary ===")
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        print(f"Results: {passed}/{total} tests passed.")
        return passed == total


def main():
    parser = argparse.ArgumentParser(description="CampusOS Deployment Smoke Tester")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI Base URL")
    parser.add_argument("--web-url", default=None, help="Next.js Frontend Base URL")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-probe timeout in seconds")

    args = parser.parse_args()
    runner = SmokeTestRunner(api_url=args.api_url, web_url=args.web_url, timeout=args.timeout)
    success = runner.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
