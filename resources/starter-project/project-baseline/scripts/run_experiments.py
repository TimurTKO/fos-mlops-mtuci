from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from mlops_course.data import load_contract, load_dataset
from mlops_course.train import build_pipeline, evaluate_pipeline


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unavailable"


def parse_values(raw: str) -> list[float]:
    values = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if len(values) < 3:
        raise ValueError("Provide at least three comma-separated C values")
    if any(value <= 0 for value in values):
        raise ValueError("All C values must be positive")
    return values


def run_experiments(
    *,
    train_path: Path,
    test_path: Path,
    contract_path: Path,
    tracking_uri: str,
    experiment_name: str,
    registered_model_name: str,
    c_values: list[float],
    max_iter: int,
    random_state: int,
    quality_gate_f1: float,
    summary_path: Path,
) -> dict:
    contract = load_contract(contract_path)
    train_frame = load_dataset(train_path, contract, require_target=True)
    test_frame = load_dataset(test_path, contract, require_target=True)
    features = list(contract["feature_columns"])
    target = contract["target_column"]

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    version_tags = {
        "git_sha": git_sha(),
        "train_sha256": sha256(train_path),
        "test_sha256": sha256(test_path),
        "contract_sha256": sha256(contract_path),
        "quality_gate_f1": str(quality_gate_f1),
    }

    runs: list[dict] = []
    for c in c_values:
        pipeline = build_pipeline(c=c, max_iter=max_iter, random_state=random_state)
        pipeline.fit(train_frame[features], train_frame[target])
        metrics = evaluate_pipeline(pipeline, test_frame, features, target)

        with mlflow.start_run(run_name=f"logreg-C-{c:g}") as active_run:
            mlflow.log_params(
                {
                    "C": c,
                    "max_iter": max_iter,
                    "random_state": random_state,
                    "train_rows": len(train_frame),
                    "test_rows": len(test_frame),
                    "feature_count": len(features),
                }
            )
            mlflow.log_metrics({f"test_{name}": value for name, value in metrics.items() if name != "rows"})
            mlflow.set_tags(version_tags)
            mlflow.log_dict(metrics, "evaluation/metrics.json")
            mlflow.log_dict(contract, "data/contract.json")

            input_example = test_frame[features].head(3)
            predictions = pipeline.predict(input_example)
            signature = infer_signature(input_example, predictions)
            model_info = mlflow.sklearn.log_model(
                sk_model=pipeline,
                name="model",
                signature=signature,
                input_example=input_example,
                pip_requirements=[
                    "scikit-learn>=1.4,<2.0",
                    "pandas>=2.1,<3.0",
                    "numpy>=1.26,<3.0",
                ],
            )

            runs.append(
                {
                    "run_id": active_run.info.run_id,
                    "model_uri": model_info.model_uri,
                    "C": c,
                    "metrics": metrics,
                    "eligible": metrics["f1"] >= quality_gate_f1,
                }
            )

    eligible = [run for run in runs if run["eligible"]]
    if not eligible:
        raise RuntimeError(f"No run passed quality gate test_f1 >= {quality_gate_f1}")
    best = max(eligible, key=lambda item: (item["metrics"]["f1"], item["metrics"]["accuracy"]))

    registered = mlflow.register_model(best["model_uri"], registered_model_name)
    client = MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)
    client.set_registered_model_alias(registered_model_name, "champion", registered.version)
    client.set_model_version_tag(
        registered_model_name,
        registered.version,
        "quality_gate",
        "PASSED",
    )
    client.set_model_version_tag(
        registered_model_name,
        registered.version,
        "source_run_id",
        best["run_id"],
    )

    champion_uri = f"models:/{registered_model_name}@champion"
    champion = mlflow.sklearn.load_model(champion_uri)
    smoke_prediction = int(champion.predict(test_frame[features].head(1))[0])

    summary = {
        "tracking_uri": tracking_uri,
        "experiment_name": experiment_name,
        "registered_model_name": registered_model_name,
        "registered_version": str(registered.version),
        "alias": "champion",
        "champion_uri": champion_uri,
        "champion_smoke_prediction": smoke_prediction,
        "quality_gate_f1": quality_gate_f1,
        "version_tags": version_tags,
        "best_run": best,
        "runs": runs,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


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
    args = parser.parse_args()

    summary = run_experiments(
        train_path=args.train,
        test_path=args.test,
        contract_path=args.contract,
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
        registered_model_name=args.registered_model_name,
        c_values=parse_values(args.C_values),
        max_iter=args.max_iter,
        random_state=args.random_state,
        quality_gate_f1=args.quality_gate_f1,
        summary_path=args.summary,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
