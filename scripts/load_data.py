"""Load salesdaily.csv into PostgreSQL and MongoDB."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.constants import ATC_COLUMNS
from app.database import get_engine, get_mongo_collection, postgres_session

DEFAULT_CSV = ROOT / "data" / "salesdaily.csv"
BATCH_SIZE = 100


def _round_total(values: dict) -> float:
    return round(sum(values.values()), 2)


def load_csv(path: Path) -> pd.DataFrame:
    df_raw = pd.read_csv(path)
    date_col = df_raw.columns[0]
    df = df_raw.rename(columns={date_col: "Date"}).copy()
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    if df["Date"].isna().any():
        df["Date"] = pd.to_datetime(df_raw[date_col], errors="coerce")
    return df.sort_values("Date").reset_index(drop=True)


def _sql_statements(sql: str) -> list[str]:
    """Split schema file into executable statements, skipping comment-only lines."""
    statements = []
    for block in sql.split(";"):
        lines = [
            line
            for line in block.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


def apply_postgres_schema() -> None:
    from app.config import POSTGRES_DATABASE

    schema_path = ROOT / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    engine = get_engine()
    with engine.begin() as conn:
        for statement in _sql_statements(sql):
            conn.execute(text(statement))
    print(f"PostgreSQL schema applied to database: {POSTGRES_DATABASE}")


def postgres_has_data() -> bool:
    with postgres_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM daily_records")).scalar()
        return count > 0


def mongo_has_data() -> bool:
    return get_mongo_collection().estimated_document_count() > 0


def bulk_load_postgres(df: pd.DataFrame) -> None:
    daily_tuples = []
    pending_categories = []

    for _, row in df.iterrows():
        categories = {col: float(row[col]) for col in ATC_COLUMNS}
        sale_date = row["Date"].date()
        daily_tuples.append((sale_date, _round_total(categories)))
        for col in ATC_COLUMNS:
            pending_categories.append((sale_date, col, round(float(row[col]), 2)))

    conn = get_engine().raw_connection()
    try:
        cur = conn.cursor()
        execute_values(
            cur,
            """
            INSERT INTO daily_records (sale_date, total_demand) VALUES %s
            ON CONFLICT (sale_date) DO UPDATE SET total_demand = EXCLUDED.total_demand
            """,
            daily_tuples,
            page_size=1000,
        )
        conn.commit()

        cur.execute("SELECT record_id, sale_date FROM daily_records")
        date_to_id = {row[1]: row[0] for row in cur.fetchall()}

        category_tuples = [
            (date_to_id[sale_date], medicine_id, units)
            for sale_date, medicine_id, units in pending_categories
        ]
        execute_values(
            cur,
            """
            INSERT INTO category_sales (record_id, medicine_id, units_sold) VALUES %s
            ON CONFLICT (record_id, medicine_id) DO UPDATE SET units_sold = EXCLUDED.units_sold
            """,
            category_tuples,
            page_size=2000,
        )
        conn.commit()
    finally:
        conn.close()


def bulk_load_mongo(df: pd.DataFrame) -> None:
    collection = get_mongo_collection()
    now = datetime.now(timezone.utc)
    documents = []

    for _, row in df.iterrows():
        categories = {col: float(row[col]) for col in ATC_COLUMNS}
        sale_date = row["Date"].date().isoformat()
        documents.append(
            {
                "record_id": sale_date,
                "sale_date": sale_date,
                "total_demand": _round_total(categories),
                "categories": categories,
                "source": "pharma_sales_daily",
                "created_at": now,
                "updated_at": now,
            }
        )

    collection.insert_many(documents, ordered=False)


def load_databases(csv_path: Path, force: bool = False) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}\n"
            "Download salesdaily.csv from Kaggle and place it in data/"
        )

    print("Applying PostgreSQL schema...")
    apply_postgres_schema()

    if not force and postgres_has_data() and mongo_has_data():
        print("Data already loaded. Use --force to reload.")
        return

    if force:
        print("Clearing existing data...")
        with postgres_session() as session:
            session.execute(text("DELETE FROM category_sales"))
            session.execute(text("DELETE FROM daily_records"))
        get_mongo_collection().delete_many({})

    df = load_csv(csv_path)
    print(f"Loading {len(df)} daily records from {csv_path.name}...")

    print("  -> PostgreSQL bulk insert...")
    bulk_load_postgres(df)
    print("  -> MongoDB bulk insert...")
    bulk_load_mongo(df)

    with postgres_session() as session:
        pg_count = session.execute(text("SELECT COUNT(*) FROM daily_records")).scalar()
    mongo_count = get_mongo_collection().estimated_document_count()
    print(f"PostgreSQL daily_records : {pg_count}")
    print(f"MongoDB documents        : {mongo_count}")
    print("Load complete.")


def main():
    parser = argparse.ArgumentParser(description="Load pharma sales CSV into databases")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to salesdaily.csv")
    parser.add_argument("--force", action="store_true", help="Clear and reload data")
    args = parser.parse_args()
    load_databases(args.csv, force=args.force)


if __name__ == "__main__":
    main()
