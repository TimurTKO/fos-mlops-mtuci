from fastapi.testclient import TestClient

from mlops_course.api import app


def test_metrics_endpoint_exposes_course_metrics():
    with TestClient(app) as client:
        client.get("/health")
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "mlops_http_requests_total" in response.text
    assert "mlops_http_request_duration_seconds" in response.text
    assert "mlops_model_ready" in response.text
    assert "mlops_service_build_info" in response.text
