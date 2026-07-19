from __future__ import annotations

from time import perf_counter

from prometheus_client import Counter, Gauge, Histogram, Info

HTTP_REQUESTS = Counter(
    "mlops_http_requests_total",
    "Total number of HTTP requests handled by the ML service.",
    ["method", "endpoint", "status"],
)
HTTP_LATENCY = Histogram(
    "mlops_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
PREDICTIONS = Counter(
    "mlops_predictions_total",
    "Number of predictions returned by class.",
    ["prediction"],
)
PREDICTION_PROBABILITY = Histogram(
    "mlops_prediction_probability",
    "Predicted positive-class probability.",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
MODEL_READY = Gauge(
    "mlops_model_ready",
    "Whether the model artifact is successfully loaded (1=yes, 0=no).",
)
BUILD_INFO = Info(
    "mlops_service_build",
    "Version metadata for the running educational ML service.",
)

KNOWN_ENDPOINTS = {"/health", "/ready", "/predict", "/metrics", "/docs", "/openapi.json"}


def configure_build_info(*, service_version: str, model_version: str, release_channel: str) -> None:
    BUILD_INFO.info(
        {
            "service_version": service_version,
            "model_version": model_version,
            "release_channel": release_channel,
        }
    )


def normalized_endpoint(path: str) -> str:
    return path if path in KNOWN_ENDPOINTS else "unmatched"


def observe_prediction(*, prediction: int, probability: float) -> None:
    PREDICTIONS.labels(prediction=str(int(prediction))).inc()
    PREDICTION_PROBABILITY.observe(float(probability))


def set_model_ready(ready: bool) -> None:
    MODEL_READY.set(1 if ready else 0)


async def prometheus_middleware(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        endpoint = normalized_endpoint(request.url.path)
        HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()
        HTTP_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
            perf_counter() - started
        )
