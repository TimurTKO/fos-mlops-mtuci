from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_FEATURES = [0.0] * 12


class SmokeTestError(RuntimeError):
    """Raised when a deployment does not satisfy the release checks."""


def request_json(url: str, *, payload: dict[str, Any] | None = None, timeout: float = 3.0) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            if response.status >= 400:
                raise SmokeTestError(f"{url} returned HTTP {response.status}")
            return json.loads(body)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise SmokeTestError(f"Request failed for {url}: {error}") from error


def wait_for_ready(base_url: str, *, timeout: float = 45.0, interval: float = 1.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            payload = request_json(f"{base_url.rstrip('/')}/ready")
            if payload.get("status") == "ready":
                return payload
        except SmokeTestError as error:
            last_error = error
        time.sleep(interval)
    raise SmokeTestError(f"Service did not become ready within {timeout:.0f}s: {last_error}")


def run_smoke_test(base_url: str, *, expected_service_version: str = "", timeout: float = 45.0) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    ready = wait_for_ready(base_url, timeout=timeout)
    health = request_json(f"{base_url}/health")

    if health.get("status") != "ok":
        raise SmokeTestError(f"Unexpected health status: {health}")
    if expected_service_version and health.get("service_version") != expected_service_version:
        raise SmokeTestError(
            "Service version mismatch: "
            f"expected {expected_service_version}, got {health.get('service_version')}"
        )

    prediction = request_json(
        f"{base_url}/predict",
        payload={"features": DEFAULT_FEATURES},
    )
    if prediction.get("prediction") not in (0, 1):
        raise SmokeTestError(f"Invalid prediction payload: {prediction}")
    probability = prediction.get("probability")
    if not isinstance(probability, (int, float)) or not 0.0 <= float(probability) <= 1.0:
        raise SmokeTestError(f"Invalid probability: {prediction}")

    return {"health": health, "ready": ready, "prediction": prediction}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the course ML API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--expected-service-version",
        default=os.getenv("EXPECTED_SERVICE_VERSION", ""),
    )
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    try:
        result = run_smoke_test(
            args.base_url,
            expected_service_version=args.expected_service_version,
            timeout=args.timeout,
        )
    except SmokeTestError as error:
        print(f"SMOKE TEST FAILED: {error}", file=sys.stderr)
        return 1

    print("SMOKE TEST PASSED")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
