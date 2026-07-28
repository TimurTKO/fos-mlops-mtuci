"""Серия воспроизводимых экспериментов в MLflow.

Студенческий каркас. Реализация выполняется в ЛР5.

Требования к результату:

- не менее трёх сопоставимых запусков на одной версии тестовой выборки;
- логирование параметров, метрик и артефактов каждого запуска;
- фиксация связи Git SHA, версии данных и параметров обучения;
- регистрация выбранной модели при выполнении quality gate по F1.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def sha256(path: Path) -> str:
    """Вернуть SHA-256 файла для фиксации версии данных."""
    # TODO (ЛР5): рассчитать контрольную сумму файла.
    raise NotImplementedError("ЛР5: реализуйте расчёт контрольной суммы")


def git_sha() -> str:
    """Вернуть текущий Git SHA или признак его отсутствия."""
    # TODO (ЛР5): получить SHA текущего коммита.
    raise NotImplementedError("ЛР5: реализуйте получение Git SHA")


def parse_values(raw: str) -> list[float]:
    """Разобрать список значений параметра из строки вида `0.1,1.0,10.0`."""
    # TODO (ЛР5): разобрать и проверить перечень значений.
    raise NotImplementedError("ЛР5: реализуйте разбор значений параметра")


def run_experiments(*args, **kwargs) -> dict:
    """Выполнить серию запусков и вернуть сводку сравнения.

    Сводка должна позволять обосновать выбор модели: параметры, метрики,
    идентификаторы запусков, версия данных и результат quality gate.
    """
    # TODO (ЛР5): выполнить запуски, залогировать их и сформировать сводку.
    raise NotImplementedError("ЛР5: реализуйте серию экспериментов")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and register reproducible MLflow experiments")
    parser.add_argument("--train", type=Path, default=Path("data/train.csv"))
    parser.add_argument("--test", type=Path, default=Path("data/test.csv"))
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    parser.add_argument("--experiment-name", default="mlops-course-experiments")
    parser.add_argument("--registered-model-name", default="mlops-course-classifier")
    parser.add_argument("--C-values", default="0.1,1.0,10.0")
    parser.add_argument("--max-iter", type=int, default=1000)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--quality-gate-f1", type=float, default=0.70)
    parser.add_argument("--summary", type=Path, default=Path("artifacts/experiment_summary.json"))
    parser.parse_args()
    raise NotImplementedError("ЛР5: реализуйте запуск серии экспериментов")


if __name__ == "__main__":
    main()
