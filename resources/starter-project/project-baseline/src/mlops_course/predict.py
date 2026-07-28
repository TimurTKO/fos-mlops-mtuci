"""Загрузка артефакта модели и одиночный инференс.

Студенческий каркас. Реализация выполняется в ЛР1 и используется API в ЛР6.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def load_model(path: str | Path):
    """Загрузить артефакт модели и проверить его структуру.

    Артефакт должен содержать как минимум ключи `pipeline` и
    `feature_columns`; иначе ожидается `ValueError`.
    """
    # TODO (ЛР1): загрузить артефакт и проверить обязательные ключи.
    raise NotImplementedError("ЛР1: реализуйте загрузку артефакта модели")


def predict_one(model_payload, values: Sequence[float]) -> dict:
    """Выполнить предсказание для одного набора значений признаков.

    Ожидаемое поведение: несовпадение числа признаков приводит к `ValueError`.
    Возвращаемый словарь содержит ключи `prediction` (int) и
    `probability` (float в диапазоне от 0 до 1).
    """
    # TODO (ЛР1): проверить длину входа и вернуть класс и вероятность.
    raise NotImplementedError("ЛР1: реализуйте одиночный инференс")
