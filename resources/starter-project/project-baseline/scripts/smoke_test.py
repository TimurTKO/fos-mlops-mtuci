"""Smoke-проверка развёрнутого сервиса.

Студенческий каркас. Реализация выполняется в ЛР6 и используется как
критерий допуска выпуска в ЛР7.

Минимальный набор проверок:

1. сервис достигает ready-состояния за отведённое время;
2. `/health` возвращает ожидаемую версию сервиса;
3. корректный запрос `/predict` возвращает предсказание по схеме;
4. некорректный запрос отделяется от ошибки сервера по коду ответа.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


class SmokeTestError(RuntimeError):
    """Проверки выпуска не выполнены."""


def request_json(url: str, *, payload: dict[str, Any] | None = None, timeout: float = 3.0) -> dict[str, Any]:
    """Выполнить HTTP-запрос и вернуть разобранный JSON-ответ."""
    # TODO (ЛР6): выполнить запрос и разобрать ответ.
    raise NotImplementedError("ЛР6: реализуйте выполнение HTTP-запроса")


def wait_for_ready(base_url: str, *, timeout: float = 45.0, interval: float = 1.0) -> dict[str, Any]:
    """Дождаться ready-состояния сервиса либо завершиться `SmokeTestError`."""
    # TODO (ЛР6): реализовать ожидание готовности с ограничением по времени.
    raise NotImplementedError("ЛР6: реализуйте ожидание готовности сервиса")


def run_smoke_test(base_url: str, *, expected_service_version: str = "", timeout: float = 45.0) -> dict[str, Any]:
    """Выполнить полный набор проверок и вернуть отчёт о результате."""
    # TODO (ЛР6): выполнить проверки готовности, версии и контракта ответа.
    raise NotImplementedError("ЛР6: реализуйте smoke-проверку")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the course ML API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--expected-version", default="")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.parse_args()
    raise NotImplementedError("ЛР6: реализуйте запуск smoke-проверки")


if __name__ == "__main__":
    sys.exit(main())
