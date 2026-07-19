from __future__ import annotations

import argparse
import time
from pathlib import Path

import httpx
import pandas as pd


def send_traffic(
    base_url: str,
    data_path: Path,
    *,
    rows: int = 100,
    delay: float = 0.02,
    invalid_every: int = 0,
) -> dict:
    frame = pd.read_csv(data_path)
    features = [column for column in frame.columns if column.startswith("feature_")]
    if not features:
        raise ValueError("No feature_* columns found")

    successful = 0
    failed = 0
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        for index in range(rows):
            values = frame.iloc[index % len(frame)][features].astype(float).tolist()
            if invalid_every and (index + 1) % invalid_every == 0:
                values = values[:-1]
            response = client.post("/predict", json={"features": values})
            if response.status_code == 200:
                successful += 1
            else:
                failed += 1
            if delay > 0:
                time.sleep(delay)
    return {"successful": successful, "failed": failed, "total": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate educational traffic for the ML API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--data", type=Path, default=Path("data/production_normal.csv"))
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.02)
    parser.add_argument("--invalid-every", type=int, default=0)
    args = parser.parse_args()
    print(send_traffic(args.base_url, args.data, rows=args.rows, delay=args.delay, invalid_every=args.invalid_every))


if __name__ == "__main__":
    main()
