"""Feature engineering aligned with the Colab notebook (Task 1 / Task 4)."""

from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from app.constants import ATC_COLUMNS, TARGET_COLUMN


def records_to_dataframe(records: List[dict]) -> pd.DataFrame:
    """Convert API/DB records into a sorted daily dataframe."""
    rows = []
    for record in records:
        sale_date = record["sale_date"]
        if isinstance(sale_date, str):
            sale_date = pd.to_datetime(sale_date)
        elif isinstance(sale_date, date):
            sale_date = pd.to_datetime(sale_date)

        row = {"Date": sale_date}
        categories = record.get("categories", record)
        for col in ATC_COLUMNS:
            row[col] = float(categories.get(col, 0))
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    df["Total_Demand"] = df[ATC_COLUMNS].sum(axis=1)
    return df


def build_features(
    dataframe: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    lag_days: tuple = (1, 3, 7, 14),
    ma_windows: tuple = (7, 14, 30),
    cross_category_cols: tuple = ("N02BA", "M01AB", "R03"),
) -> pd.DataFrame:
    """Mirror of the Colab `build_features` function."""
    feat = dataframe.copy()

    feat["Year"] = feat["Date"].dt.year
    feat["Month"] = feat["Date"].dt.month
    feat["Hour"] = feat["Hour"] if "Hour" in feat.columns else feat["Date"].dt.dayofyear
    feat["DOW"] = feat["Date"].dt.dayofweek
    feat["DayOfYear"] = feat["Date"].dt.dayofyear
    feat["IsWeekend"] = (feat["DOW"] >= 5).astype(int)

    for lag in lag_days:
        feat[f"{target_col}_lag_{lag}"] = feat[target_col].shift(lag)

    for window in ma_windows:
        feat[f"{target_col}_ma_{window}"] = (
            feat[target_col].shift(1).rolling(window, min_periods=1).mean()
        )
        feat[f"Total_Demand_ma_{window}"] = (
            feat["Total_Demand"].shift(1).rolling(window, min_periods=1).mean()
        )

    for col in cross_category_cols:
        feat[f"{col}_lag_1"] = feat[col].shift(1)

    return feat.dropna().reset_index(drop=True)


def build_prediction_row(
    records: List[dict],
    feature_columns: List[str],
    target_col: str = TARGET_COLUMN,
    lag_days: tuple = (1, 3, 7, 14),
    ma_windows: tuple = (7, 14, 30),
    cross_category_cols: tuple = ("N02BA", "M01AB", "R03"),
) -> Optional[pd.DataFrame]:
    """Return a single feature row for the most recent date in the history window."""
    if not records:
        return None

    df = records_to_dataframe(records)
    features = build_features(
        df,
        target_col=target_col,
        lag_days=lag_days,
        ma_windows=ma_windows,
        cross_category_cols=cross_category_cols,
    )
    if features.empty:
        return None

    latest = features.iloc[[-1]]
    missing = [col for col in feature_columns if col not in latest.columns]
    if missing:
        raise ValueError(f"Missing engineered features: {missing}")

    return latest[feature_columns]
