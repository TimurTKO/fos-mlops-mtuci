"""Диагностический помощник расследования инцидента.

Студенческий каркас. Реализация выполняется в ЛР9.

Скрипт не заменяет инженерное заключение: он собирает доказательства и
предлагает гипотезы. Классификация инцидента должна различать нарушение
контракта данных, сдвиг распределения и снижение измеренного качества.

Шаблон итогового документа — `monitoring/postmortem-template.md`,
описание учебных сценариев — `monitoring/incident-scenarios.md`.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def classify_incident(*args, **kwargs) -> dict:
    """Определить тип инцидента по собранным доказательствам."""
    # TODO (ЛР9): различить нарушение контракта, drift и падение качества.
    raise NotImplementedError("ЛР9: реализуйте классификацию инцидента")


def render_postmortem(report: dict) -> str:
    """Сформировать заготовку постмортема из собранных доказательств."""
    # TODO (ЛР9): заполнить разделы симптома, гипотез и корневой причины.
    raise NotImplementedError("ЛР9: реализуйте формирование постмортема")


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate an educational incident scenario")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/incident"))
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    parser.add_argument("--f1-threshold", type=float, default=0.75)
    parser.parse_args()
    raise NotImplementedError("ЛР9: реализуйте запуск расследования")


if __name__ == "__main__":
    main()
