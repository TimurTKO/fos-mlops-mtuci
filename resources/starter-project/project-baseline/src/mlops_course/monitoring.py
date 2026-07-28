"""Метрики сервиса для Prometheus.

Студенческий каркас. Реализация выполняется в ЛР8.

Рекомендуемый минимальный состав метрик:

- счётчик HTTP-запросов с labels метода, endpoint и кода ответа;
- гистограмма длительности HTTP-запросов;
- счётчик предсказаний по классам;
- гистограмма вероятности положительного класса;
- gauge готовности модели;
- info с версиями сервиса, модели и канала выпуска.

Кардинальность labels должна оставаться ограниченной: путь запроса
приводится к известному набору endpoint, иначе используется `unmatched`.
"""

from __future__ import annotations

KNOWN_ENDPOINTS = {"/health", "/ready", "/predict", "/metrics", "/docs", "/openapi.json"}

# TODO (ЛР8): объявить метрики prometheus_client (Counter, Histogram, Gauge, Info).


def configure_build_info(*, service_version: str, model_version: str, release_channel: str) -> None:
    """Зафиксировать версии сервиса, модели и канала выпуска в метрике info."""
    # TODO (ЛР8): заполнить Info-метрику переданными версиями.
    raise NotImplementedError("ЛР8: реализуйте публикацию сведений о сборке")


def normalized_endpoint(path: str) -> str:
    """Привести путь запроса к известному endpoint или к значению `unmatched`."""
    # TODO (ЛР8): ограничить кардинальность label endpoint.
    raise NotImplementedError("ЛР8: реализуйте нормализацию endpoint")


def observe_prediction(*, prediction: int, probability: float) -> None:
    """Учесть предсказание в счётчике классов и гистограмме вероятностей."""
    # TODO (ЛР8): обновить метрики предсказаний.
    raise NotImplementedError("ЛР8: реализуйте учёт предсказаний")


def set_model_ready(ready: bool) -> None:
    """Обновить gauge готовности модели значением 1 или 0."""
    # TODO (ЛР8): обновить gauge готовности модели.
    raise NotImplementedError("ЛР8: реализуйте признак готовности модели")


async def prometheus_middleware(request, call_next):
    """Учитывать количество и длительность HTTP-запросов, кроме `/metrics`."""
    # TODO (ЛР8): измерить длительность запроса и обновить метрики,
    #             корректно учитывая ошибочные ответы.
    raise NotImplementedError("ЛР8: реализуйте middleware сбора метрик")
