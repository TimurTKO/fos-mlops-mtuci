from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_has_healthcheck_and_smoke_profile():
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert "api" in services
    assert "healthcheck" in services["api"]
    assert services["api"]["restart"] == "unless-stopped"
    assert services["smoke"]["profiles"] == ["validation"]
    assert services["smoke"]["depends_on"]["api"]["condition"] == "service_healthy"


def test_dockerfile_runs_as_non_root_and_exposes_api():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.11-slim" in dockerfile
    assert "USER app" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "SIMULATE_STARTUP_FAILURE" in dockerfile


def test_dockerignore_excludes_sensitive_and_generated_files():
    ignored = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())
    assert ".env" in ignored
    assert ".git" in ignored
    assert "mlflow.db" in ignored
    assert "mlruns" in ignored
    assert "data" in ignored
    assert "artifacts" in ignored
