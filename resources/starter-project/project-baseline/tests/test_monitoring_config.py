from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_contains_pinned_monitoring_services():
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert services["prometheus"]["image"] == "prom/prometheus:v3.11.2"
    assert services["grafana"]["image"] == "grafana/grafana:13.0.3"
    assert services["prometheus"]["profiles"] == ["monitoring"]
    assert services["grafana"]["profiles"] == ["monitoring"]


def test_prometheus_scrapes_api_and_loads_rules():
    config = yaml.safe_load(
        (ROOT / "monitoring/prometheus/prometheus.yml").read_text(encoding="utf-8")
    )
    assert "/etc/prometheus/rules.yml" in config["rule_files"]
    targets = config["scrape_configs"][0]["static_configs"][0]["targets"]
    assert "api:8000" in targets


def test_grafana_dashboard_contains_expected_promql():
    dashboard = json.loads(
        (ROOT / "monitoring/grafana/dashboards/mlops-course.json").read_text(
            encoding="utf-8"
        )
    )
    expressions = [
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
        if "expr" in target
    ]
    assert any("mlops_http_requests_total" in expression for expression in expressions)
    assert any("mlops_predictions_total" in expression for expression in expressions)
    assert dashboard["uid"] == "mlops-course-service"
