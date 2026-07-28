"""Обучение и оценка базовой модели классификации.

Студенческий каркас. Реализация выполняется в ЛР1, пороги качества
добавляются в ЛР2, параметры выносятся в конфигурацию в ЛР4.

Исходный прототип модели приведён в `notebooks/01_ml_prototype.ipynb`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.pipeline import Pipeline

from mlops_course.data import load_contract, load_dataset


def build_pipeline(*, c: float = 1.0, max_iter: int = 1000, random_state: int = 42) -> Pipeline:
    """Собрать пайплайн классификации из явно переданных параметров.

    Ожидаемое поведение: `c <= 0` и `max_iter < 10` приводят к `ValueError`.
    """
    # TODO (ЛР1): проверить параметры и собрать Pipeline из масштабирования
    #             признаков и классификатора (см. прототип в ноутбуке).
    raise NotImplementedError("ЛР1: реализуйте сборку пайплайна")


def evaluate_pipeline(pipeline: Pipeline, frame, feature_columns: list[str], target_column: str) -> dict:
    """Рассчитать метрики качества на переданной выборке.

    Возвращаемый словарь содержит ключи `accuracy`, `precision`, `recall`,
    `f1` и `rows`.
    """
    # TODO (ЛР1): получить предсказания и рассчитать метрики.
    raise NotImplementedError("ЛР1: реализуйте расчёт метрик")


def train_model(
    data_path: Path,
    contract_path: Path,
    model_path: Path,
    metrics_path: Path,
    test_data_path: Path | None = None,
    *,
    c: float = 1.0,
    max_iter: int = 1000,
    random_state: int = 42,
) -> dict:
    """Обучить модель, сохранить артефакт и метрики, вернуть метрики.

    Артефакт модели должен содержать сам пайплайн, список признаков, версию
    контракта и параметры обучения: эти сведения нужны инференсу и
    прослеживаемости в ЛР4–ЛР5.

    Метрики рассчитываются на независимой тестовой выборке.
    """
    # TODO (ЛР1): загрузить контракт и выборки, обучить пайплайн.
    # TODO (ЛР1): сохранить артефакт модели и файл метрик.
    # TODO (ЛР2): согласовать пороговое значение F1 с автоматическими проверками.
    raise NotImplementedError("ЛР1: реализуйте обучение и сохранение модели")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the course baseline classifier")
    parser.add_argument("--data", type=Path, default=Path("data/train.csv"))
    parser.add_argument("--test-data", type=Path, default=Path("data/test.csv"))
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("artifacts/metrics.json"))
    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument("--max-iter", type=int, default=1000)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    metrics = train_model(
        args.data,
        args.contract,
        args.model,
        args.metrics,
        args.test_data,
        c=args.C,
        max_iter=args.max_iter,
        random_state=args.random_state,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
