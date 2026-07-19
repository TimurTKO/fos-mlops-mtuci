from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
N_FEATURES = 12
FEATURE_COLUMNS = [f"feature_{i:02d}" for i in range(N_FEATURES)]
TARGET_COLUMN = "target"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frame(x: np.ndarray, y: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(x, columns=FEATURE_COLUMNS)
    frame[TARGET_COLUMN] = y.astype(int)
    return frame


def generate(output_dir: Path, random_state: int = RANDOM_STATE) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    x, y = make_classification(
        n_samples=2400,
        n_features=N_FEATURES,
        n_informative=7,
        n_redundant=3,
        n_repeated=0,
        n_classes=2,
        weights=[0.55, 0.45],
        class_sep=1.2,
        flip_y=0.03,
        random_state=random_state,
    )

    x_train, x_temp, y_train, y_temp = train_test_split(
        x, y, test_size=0.4, stratify=y, random_state=random_state
    )
    x_test, x_prod, y_test, y_prod = train_test_split(
        x_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=random_state
    )

    train = _frame(x_train, y_train)
    test = _frame(x_test, y_test)
    production_normal = _frame(x_prod, y_prod)

    # Обновлённая версия для сценария DVC: дополнительные объекты с тем же контрактом.
    x_update, y_update = make_classification(
        n_samples=300,
        n_features=N_FEATURES,
        n_informative=7,
        n_redundant=3,
        weights=[0.52, 0.48],
        class_sep=1.15,
        flip_y=0.035,
        random_state=random_state + 1,
    )
    updated = pd.concat([train, _frame(x_update, y_update)], ignore_index=True)

    # Контролируемый data drift: меняем распределение нескольких признаков.
    drifted = production_normal.copy()
    drifted["feature_00"] = drifted["feature_00"] + 1.75
    drifted["feature_01"] = drifted["feature_01"] * 1.35
    drifted["feature_02"] = drifted["feature_02"] - 1.10

    # Сценарий деградации: нарушаем информативность части признаков.
    incident_degraded = production_normal.copy()
    rng = np.random.default_rng(random_state + 2)
    for column in ["feature_00", "feature_01", "feature_02", "feature_03"]:
        incident_degraded[column] = rng.permutation(incident_degraded[column].to_numpy())

    # Сценарий нарушения контракта данных.
    incident_bad_schema = production_normal.copy().drop(columns=["feature_03"])
    incident_bad_schema.loc[incident_bad_schema.index[:12], "feature_07"] = np.nan
    incident_bad_schema["feature_05"] = incident_bad_schema["feature_05"].astype(object)
    incident_bad_schema.loc[incident_bad_schema.index[:8], "feature_05"] = "invalid"

    datasets = {
        "train.csv": train,
        "test.csv": test,
        "production_normal.csv": production_normal,
        "updated.csv": updated,
        "production_drift.csv": drifted,
        "incident_degraded.csv": incident_degraded,
        "incident_bad_schema.csv": incident_bad_schema,
    }

    files = {}
    for filename, frame in datasets.items():
        path = output_dir / filename
        frame.to_csv(path, index=False)
        files[filename] = {
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "target_rate": float(frame[TARGET_COLUMN].mean()) if TARGET_COLUMN in frame else None,
            "sha256": _sha256(path),
        }

    metadata = {
        "generator": "sklearn.datasets.make_classification",
        "random_state": random_state,
        "task": "synthetic_binary_classification",
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "files": files,
        "usage": {
            "train.csv": "обучение базовой модели",
            "test.csv": "оценка качества и регрессионные тесты",
            "production_normal.csv": "нормальный поток данных",
            "updated.csv": "новая версия данных для DVC",
            "production_drift.csv": "сценарий data drift",
            "incident_degraded.csv": "сценарий деградации качества",
            "incident_bad_schema.csv": "сценарий нарушения контракта данных",
        },
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducible MLOps course datasets")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "generated")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE)
    args = parser.parse_args()
    metadata = generate(args.output_dir, args.random_state)
    print(json.dumps({"status": "ok", "output_dir": str(args.output_dir), "files": list(metadata["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
