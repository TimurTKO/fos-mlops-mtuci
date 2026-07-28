"""HTTP-сервис инференса.

Студенческий каркас. Базовые endpoint реализуются в ЛР2 и ЛР6, метрики
подключаются в ЛР8. Требования к API приведены в
`M3-deployment/kim-06-api-compose.md`.

Обязательный контур:

- `GET  /health`  — состояние сервиса и версии, всегда HTTP 200;
- `GET  /ready`   — готовность модели, HTTP 503 при недоступном артефакте;
- `GET  /metrics` — экспорт метрик в формате Prometheus (ЛР8);
- `POST /predict` — предсказание, HTTP 422 при нарушении схемы запроса.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/model.joblib"))
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "dev")
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-dev")
RELEASE_CHANNEL = os.getenv("RELEASE_CHANNEL", "local")
_model = None


class PredictionRequest(BaseModel):
    """Схема запроса. Число признаков должно соответствовать контракту данных."""

    features: list[float] = Field(min_length=12, max_length=12)


class PredictionResponse(BaseModel):
    """Схема ответа сервиса."""

    prediction: int
    probability: float


def reset_model_cache() -> None:
    """Сбросить кэш модели; используется в изолированных тестах."""
    # TODO (ЛР2): сбросить глобальный кэш и признак готовности модели.
    raise NotImplementedError("ЛР2: реализуйте сброс кэша модели")


def get_model():
    """Вернуть загруженную модель, загрузив её при первом обращении.

    При отсутствии артефакта ожидается `FileNotFoundError`.
    """
    # TODO (ЛР2): реализовать ленивую загрузку модели и обработку ошибок.
    raise NotImplementedError("ЛР2: реализуйте ленивую загрузку модели")


app = FastAPI(title="MLOps Course API", version=SERVICE_VERSION)

# TODO (ЛР8): подключить middleware сбора метрик из mlops_course.monitoring
#             и добавить endpoint /metrics.


@app.get("/health")
def health() -> dict:
    """Вернуть состояние сервиса, версию сервиса и версию модели."""
    # TODO (ЛР2): вернуть сведения о состоянии сервиса без обращения к модели.
    raise NotImplementedError("ЛР2: реализуйте endpoint /health")


@app.get("/ready")
def ready() -> dict:
    """Подтвердить готовность модели к обслуживанию запросов."""
    # TODO (ЛР6): вернуть HTTP 503, если модель недоступна.
    raise NotImplementedError("ЛР6: реализуйте endpoint /ready")


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Выполнить предсказание по валидированному запросу."""
    # TODO (ЛР2): выполнить инференс и вернуть ответ по схеме.
    # TODO (ЛР8): зафиксировать метрики предсказания.
    raise NotImplementedError("ЛР2: реализуйте endpoint /predict")
