# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1     PIP_NO_CACHE_DIR=1     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY scripts/generate_data.py ./scripts/generate_data.py

RUN python -m pip install --upgrade pip     && python -m pip install .

ARG MODEL_C=1.0
ARG MODEL_RANDOM_STATE=42
RUN python scripts/generate_data.py --output-dir data --random-state ${MODEL_RANDOM_STATE}     && python -m mlops_course.train        --data data/train.csv        --test-data data/test.csv        --contract configs/data_contract.json        --model artifacts/model.joblib        --metrics artifacts/metrics.json        --C ${MODEL_C}        --random-state ${MODEL_RANDOM_STATE}

FROM python:3.11-slim AS runtime

ARG SERVICE_VERSION=dev
ARG MODEL_VERSION=baseline-dev

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PYTHONPATH=/app/src     MODEL_PATH=/app/artifacts/model.joblib     SERVICE_VERSION=${SERVICE_VERSION}     MODEL_VERSION=${MODEL_VERSION}     RELEASE_CHANNEL=local     PRELOAD_MODEL=1     SIMULATE_STARTUP_FAILURE=0

RUN groupadd --system app     && useradd --system --gid app --home-dir /app app

WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY --from=builder /build/artifacts ./artifacts
COPY --from=builder /build/configs ./configs
COPY --from=builder /build/src ./src
COPY scripts/smoke_test.py ./scripts/smoke_test.py

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2).read()" || exit 1

CMD ["uvicorn", "mlops_course.api:app", "--host", "0.0.0.0", "--port", "8000"]
