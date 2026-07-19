PYTHON ?= python

install:
	$(PYTHON) -m pip install -e ".[dev]"

install-mlops:
	$(PYTHON) -m pip install -e ".[all]"

data:
	$(PYTHON) scripts/generate_data.py --output-dir data

train:
	$(PYTHON) -m mlops_course.train

test:
	pytest

dvc-repro:
	dvc repro

experiments:
	$(PYTHON) scripts/run_experiments.py

mlflow-ui:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

api:
	uvicorn mlops_course.api:app --reload

docker-config:
	docker compose config

docker-build:
	docker compose build api

compose-up:
	docker compose up -d api

monitoring-up:
	docker compose --profile monitoring up -d --build

monitoring-down:
	docker compose --profile monitoring down

traffic-normal:
	$(PYTHON) scripts/generate_traffic.py --data data/production_normal.csv --rows 200

traffic-drift:
	$(PYTHON) scripts/generate_traffic.py --data data/production_drift.csv --rows 200 --invalid-every 25

drift-report:
	$(PYTHON) scripts/analyze_drift.py --reference data/production_normal.csv --current data/production_drift.csv --output-dir reports/drift

incident-report:
	$(PYTHON) scripts/investigate_incident.py --reference data/production_normal.csv --current data/incident_degraded.csv --output-dir reports/incident

smoke:
	$(PYTHON) scripts/smoke_test.py --base-url http://127.0.0.1:8000

compose-smoke:
	docker compose --profile validation run --rm smoke

compose-down:
	docker compose down

release-status:
	$(PYTHON) scripts/release_manager.py status
