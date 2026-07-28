"""Анализ сдвига данных и измеренного качества.

Студенческий каркас. Реализация выполняется в ЛР8.

Важное методическое ограничение: PSI — только один из индикаторов.
Высокий PSI не доказывает concept drift, а его отсутствие не гарантирует
сохранение качества модели. Отчёт должен разделять изменение данных и
измеренное снижение качества.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    """Вернуть SHA-256 файла данных для прослеживаемости отчёта."""
    # TODO (ЛР8): рассчитать контрольную сумму файла.
    raise NotImplementedError("ЛР8: реализуйте расчёт контрольной суммы")


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Рассчитать PSI между эталонным и текущим распределением признака."""
    # TODO (ЛР8): реализовать разбиение на интервалы и расчёт PSI.
    raise NotImplementedError("ЛР8: реализуйте расчёт PSI")


def standardized_mean_difference(reference: np.ndarray, current: np.ndarray) -> float:
    """Рассчитать стандартизованную разность средних значений признака."""
    # TODO (ЛР8): реализовать расчёт стандартизованной разности средних.
    raise NotImplementedError("ЛР8: реализуйте расчёт разности средних")


def evaluate_model(model_path: Path, frame: pd.DataFrame, features: list[str], target: str) -> dict:
    """Оценить качество модели на переданной выборке, если метки доступны."""
    # TODO (ЛР8): рассчитать метрики или явно указать отсутствие меток.
    raise NotImplementedError("ЛР8: реализуйте оценку качества")


def analyze_pair(*args, **kwargs) -> dict:
    """Сравнить эталонный и текущий наборы данных и вернуть отчёт."""
    # TODO (ЛР8): рассчитать признаковые метрики сдвига и качество модели.
    raise NotImplementedError("ЛР8: реализуйте сравнение наборов данных")


def render_markdown(report: dict) -> str:
    """Сформировать Markdown-представление отчёта о сдвиге."""
    # TODO (ЛР8): оформить отчёт с разделением drift и снижения качества.
    raise NotImplementedError("ЛР8: реализуйте формирование отчёта")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze data drift and measured quality")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/drift"))
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    parser.add_argument("--f1-threshold", type=float, default=0.75)
    parser.add_argument("--fail-on-drift", action="store_true")
    parser.parse_args()
    raise NotImplementedError("ЛР8: реализуйте запуск анализа сдвига")


if __name__ == "__main__":
    main()
