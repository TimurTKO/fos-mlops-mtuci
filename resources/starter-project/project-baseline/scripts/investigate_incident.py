from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

from mlops_course.data import load_contract, load_dataset

MODULE_PATH = Path(__file__).with_name("analyze_drift.py")
spec = importlib.util.spec_from_file_location("analyze_drift", MODULE_PATH)
analyze_drift = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(analyze_drift)


def classify_incident(
    reference_path: Path,
    current_path: Path,
    contract_path: Path,
    model_path: Path,
    *,
    psi_threshold: float = 0.20,
    f1_threshold: float = 0.75,
) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    contract = load_contract(contract_path)
    try:
        load_dataset(current_path, contract, require_target=True)
    except (ValueError, TypeError) as error:
        return {
            "started_at": started_at,
            "scenario": "data_contract_violation",
            "severity": "high",
            "root_cause": str(error),
            "evidence": {"current_path": str(current_path)},
            "recommended_action": "Изолировать входной набор, восстановить корректную версию данных и не допускать его к инференсу до прохождения контракта.",
            "verification": ["contract tests", "pytest", "smoke test"],
        }

    report = analyze_drift.analyze_pair(
        reference_path,
        current_path,
        contract_path,
        model_path,
        psi_threshold=psi_threshold,
        f1_threshold=f1_threshold,
    )
    summary = report["summary"]

    if summary["drift_detected"] and summary["quality_degraded"]:
        scenario = "data_drift_with_quality_degradation"
        severity = "high"
        action = "Ограничить выпуск, проверить актуальность меток и подготовить переобученную модель с полным quality gate; при влиянии на пользователей откатить модель или поток данных."
    elif summary["drift_detected"] and not summary["quality_degraded"]:
        scenario = "data_drift_without_confirmed_quality_degradation"
        severity = "medium"
        action = "Продолжить усиленное наблюдение, запросить актуальные метки и не выполнять автоматическое переобучение только по факту PSI."
    elif not summary["drift_detected"] and summary["quality_degraded"]:
        scenario = "quality_degradation_without_univariate_data_drift"
        severity = "high"
        action = "Проверить изменение связи признаков с целью, ошибки разметки и сегменты качества; откатить модель или данные при подтверждённом влиянии."
    else:
        scenario = "no_confirmed_incident"
        severity = "low"
        action = "Зафиксировать результаты и продолжить штатный мониторинг."

    return {
        "started_at": started_at,
        "scenario": scenario,
        "severity": severity,
        "root_cause": "Учебная автоматическая классификация; корневая причина должна быть подтверждена студентом.",
        "evidence": report,
        "recommended_action": action,
        "verification": ["pytest", "API readiness", "smoke test", "repeat drift/quality analysis"],
    }


def render_postmortem(report: dict) -> str:
    return f"""# Постмортем учебного инцидента

## Сводка

- Начало: `{report['started_at']}`
- Сценарий: **{report['scenario']}**
- Предварительная критичность: **{report['severity']}**

## Наблюдаемый эффект

[Заполняется студентом: какой компонент или показатель изменился и кого это затронуло.]

## Доказательства

Автоматический отчёт сохранён в `incident-report.json`. Студент должен добавить ссылки на метрики, логи, версии данных, модели и кода.

## Гипотезы и проверки

1. [Гипотеза 1 и способ проверки]
2. [Гипотеза 2 и способ проверки]

## Корневая причина

{report['root_cause']}

## Реакция

Рекомендация помощника: {report['recommended_action']}

Фактически выбранное действие и обоснование: [заполняется студентом].

## Восстановление и проверка

- [ ] автоматические тесты;
- [ ] readiness;
- [ ] smoke-тест;
- [ ] повторный анализ drift/качества;
- [ ] проверка отсутствия секретов.

## Предупреждение повторения

[Конкретные изменения тестов, мониторинга, процесса выпуска или контракта данных.]
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify an educational MLOps incident")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/incident"))
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    parser.add_argument("--f1-threshold", type=float, default=0.75)
    args = parser.parse_args()

    report = classify_incident(
        args.reference,
        args.current,
        args.contract,
        args.model,
        psi_threshold=args.psi_threshold,
        f1_threshold=args.f1_threshold,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "incident-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "postmortem.md").write_text(render_postmortem(report), encoding="utf-8")
    print(json.dumps({"scenario": report["scenario"], "severity": report["severity"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
