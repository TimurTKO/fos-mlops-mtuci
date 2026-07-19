from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from mlops_course.data import load_contract, load_dataset


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    if reference.size == 0 or current.size == 0:
        raise ValueError("PSI requires non-empty arrays")

    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    epsilon = 1e-6
    ref_ratio = np.maximum(ref_counts / ref_counts.sum(), epsilon)
    cur_ratio = np.maximum(cur_counts / cur_counts.sum(), epsilon)
    return float(np.sum((cur_ratio - ref_ratio) * np.log(cur_ratio / ref_ratio)))


def standardized_mean_difference(reference: np.ndarray, current: np.ndarray) -> float:
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    pooled = math.sqrt((float(np.var(ref)) + float(np.var(cur))) / 2.0)
    if pooled == 0:
        return 0.0
    return float((float(np.mean(cur)) - float(np.mean(ref))) / pooled)


def evaluate_model(model_path: Path, frame: pd.DataFrame, features: list[str], target: str) -> dict:
    payload = joblib.load(model_path)
    pipeline = payload["pipeline"]
    predictions = pipeline.predict(frame[features])
    return {
        "accuracy": float(accuracy_score(frame[target], predictions)),
        "f1": float(f1_score(frame[target], predictions, zero_division=0)),
        "rows": int(len(frame)),
    }


def analyze_pair(
    reference_path: Path,
    current_path: Path,
    contract_path: Path,
    model_path: Path | None = None,
    *,
    psi_threshold: float = 0.20,
    f1_threshold: float = 0.75,
) -> dict:
    contract = load_contract(contract_path)
    reference = load_dataset(reference_path, contract, require_target=True)
    current = load_dataset(current_path, contract, require_target=True)
    features = list(contract["feature_columns"])
    target = contract["target_column"]

    feature_results = []
    for feature in features:
        psi = population_stability_index(reference[feature].to_numpy(), current[feature].to_numpy())
        smd = standardized_mean_difference(reference[feature].to_numpy(), current[feature].to_numpy())
        feature_results.append(
            {
                "feature": feature,
                "psi": psi,
                "standardized_mean_difference": smd,
                "drift_detected": bool(psi >= psi_threshold),
                "reference_mean": float(reference[feature].mean()),
                "current_mean": float(current[feature].mean()),
            }
        )

    model_quality = None
    quality_degraded = None
    if model_path and model_path.exists():
        reference_quality = evaluate_model(model_path, reference, features, target)
        current_quality = evaluate_model(model_path, current, features, target)
        model_quality = {"reference": reference_quality, "current": current_quality}
        quality_degraded = bool(current_quality["f1"] < f1_threshold)

    drifted = [item["feature"] for item in feature_results if item["drift_detected"]]
    return {
        "reference": {
            "path": str(reference_path),
            "sha256": sha256(reference_path),
            "rows": int(len(reference)),
        },
        "current": {
            "path": str(current_path),
            "sha256": sha256(current_path),
            "rows": int(len(current)),
        },
        "thresholds": {"psi": psi_threshold, "f1": f1_threshold},
        "summary": {
            "drift_detected": bool(drifted),
            "drifted_feature_count": len(drifted),
            "drifted_features": drifted,
            "quality_degraded": quality_degraded,
        },
        "features": feature_results,
        "model_quality": model_quality,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Отчёт о drift и качестве модели",
        "",
        f"- Reference: `{report['reference']['path']}`",
        f"- Current: `{report['current']['path']}`",
        f"- PSI threshold: `{report['thresholds']['psi']}`",
        f"- Drift detected: **{summary['drift_detected']}**",
        f"- Drifted features: **{summary['drifted_feature_count']}**",
    ]
    if summary["quality_degraded"] is not None:
        lines.append(f"- Quality degraded: **{summary['quality_degraded']}**")
        q = report["model_quality"]
        lines.extend(
            [
                f"- Reference F1: `{q['reference']['f1']:.4f}`",
                f"- Current F1: `{q['current']['f1']:.4f}`",
            ]
        )
    lines.extend(["", "## Признаки", "", "| Признак | PSI | SMD | Drift |", "|---|---:|---:|:---:|"])
    for item in sorted(report["features"], key=lambda value: value["psi"], reverse=True):
        lines.append(
            f"| {item['feature']} | {item['psi']:.4f} | {item['standardized_mean_difference']:.4f} | {'да' if item['drift_detected'] else 'нет'} |"
        )
    lines.extend(
        [
            "",
            "## Интерпретация",
            "",
            "PSI является учебным индикатором изменения маргинального распределения признака. Он не доказывает concept drift и не заменяет оценку качества на актуальных размеченных данных.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare reference and current ML datasets")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path("configs/data_contract.json"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/drift"))
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    parser.add_argument("--f1-threshold", type=float, default=0.75)
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args()

    report = analyze_pair(
        args.reference,
        args.current,
        args.contract,
        args.model,
        psi_threshold=args.psi_threshold,
        f1_threshold=args.f1_threshold,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "drift-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "drift-report.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.fail_on_drift and report["summary"]["drift_detected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
