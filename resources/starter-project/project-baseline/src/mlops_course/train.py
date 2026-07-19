from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlops_course.data import load_contract, load_dataset


def build_pipeline(*, c: float = 1.0, max_iter: int = 1000, random_state: int = 42) -> Pipeline:
    """Create the baseline classification pipeline from explicit parameters."""
    if c <= 0:
        raise ValueError("C must be positive")
    if max_iter < 10:
        raise ValueError("max_iter must be at least 10")
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(C=c, max_iter=max_iter, random_state=random_state),
            ),
        ]
    )


def evaluate_pipeline(pipeline: Pipeline, frame, feature_columns: list[str], target_column: str) -> dict:
    predictions = pipeline.predict(frame[feature_columns])
    return {
        "accuracy": float(accuracy_score(frame[target_column], predictions)),
        "precision": float(precision_score(frame[target_column], predictions, zero_division=0)),
        "recall": float(recall_score(frame[target_column], predictions, zero_division=0)),
        "f1": float(f1_score(frame[target_column], predictions, zero_division=0)),
        "rows": int(len(frame)),
    }


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
    contract = load_contract(contract_path)
    train_frame = load_dataset(data_path, contract, require_target=True)
    test_frame = load_dataset(test_data_path or data_path, contract, require_target=True)
    features = list(contract["feature_columns"])
    target = contract["target_column"]

    pipeline = build_pipeline(c=c, max_iter=max_iter, random_state=random_state)
    pipeline.fit(train_frame[features], train_frame[target])

    train_metrics = evaluate_pipeline(pipeline, train_frame, features, target)
    test_metrics = evaluate_pipeline(pipeline, test_frame, features, target)
    metrics = {
        "train_accuracy": train_metrics["accuracy"],
        "train_f1": train_metrics["f1"],
        "test_accuracy": test_metrics["accuracy"],
        "test_precision": test_metrics["precision"],
        "test_recall": test_metrics["recall"],
        "test_f1": test_metrics["f1"],
        # Compatibility alias used by the first module and DVC metrics view.
        "f1": test_metrics["f1"],
        "train_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "features": len(features),
        "C": float(c),
        "max_iter": int(max_iter),
        "random_state": int(random_state),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_columns": features,
            "contract_version": contract.get("contract_version", "unknown"),
            "training_parameters": {
                "C": float(c),
                "max_iter": int(max_iter),
                "random_state": int(random_state),
            },
        },
        model_path,
    )
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


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
