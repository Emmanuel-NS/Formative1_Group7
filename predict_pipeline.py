"""
Task 4: End-to-end prediction pipeline.

1. Fetch recent records from the FastAPI server
2. Engineer lag / moving-average features (same logic as Colab)
3. Load trained model from pharma_demand_model.pkl
4. Print next-day demand forecast
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import joblib
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.config import API_HOST, API_PORT, MODEL_PATH
from app.constants import TARGET_COLUMN
from app.preprocessing import build_prediction_row

API_BASE = f"http://{API_HOST}:{API_PORT}"
HISTORY_DAYS = 45


def fetch_latest_record() -> dict:
    response = requests.get(f"{API_BASE}/api/records/latest", timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload["records"]:
        raise RuntimeError("No records returned from /api/records/latest")
    return payload["records"][0].model_dump() if hasattr(payload["records"][0], "model_dump") else payload["records"][0]


def fetch_history(end_date: date) -> list[dict]:
    start_date = end_date - timedelta(days=HISTORY_DAYS)
    response = requests.get(
        f"{API_BASE}/api/records/range",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "source": "sql",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["records"]


def main():
    print("=" * 60)
    print("PHARMA DEMAND FORECAST PIPELINE (Task 4)")
    print("=" * 60)

    if not Path(MODEL_PATH).exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Run the Colab notebook and download pharma_demand_model.pkl first."
        )

    print("\n[1/4] Fetching latest record from API...")
    latest = fetch_latest_record()
    latest_date = latest["sale_date"]
    if isinstance(latest_date, str):
        latest_date = date.fromisoformat(latest_date)
    print(f"      Latest date: {latest_date} | N02BE today: {latest['categories'][TARGET_COLUMN]}")

    print("\n[2/4] Fetching history for feature engineering...")
    history = fetch_history(latest_date)
    record_dicts = [
        {
            "sale_date": r["sale_date"] if isinstance(r, dict) else r.sale_date,
            "categories": r["categories"] if isinstance(r, dict) else r.categories,
        }
        for r in history
    ]
    print(f"      Records in window: {len(record_dicts)}")

    print("\n[3/4] Loading model and building features...")
    artifacts = joblib.load(MODEL_PATH)
    model = artifacts["model"]
    feature_columns = artifacts["feature_columns"]

    feature_row = build_prediction_row(
        record_dicts,
        feature_columns=feature_columns,
        target_col=artifacts.get("target_column", TARGET_COLUMN),
        lag_days=tuple(artifacts.get("lag_days", (1, 3, 7, 14))),
        ma_windows=tuple(artifacts.get("ma_windows", (7, 14, 30))),
        cross_category_cols=tuple(artifacts.get("cross_category_cols", ("N02BA", "M01AB", "R03"))),
    )
    if feature_row is None:
        raise RuntimeError("Not enough history to build features. Load more data.")

    print("\n[4/4] Generating forecast...")
    prediction = float(model.predict(feature_row)[0])

    print("\n" + "=" * 60)
    print(f"Predicted {TARGET_COLUMN} demand for next day: {prediction:.2f} units")
    print(f"Model experiment: {artifacts.get('best_experiment', 'unknown')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
