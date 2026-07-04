"""PostgreSQL repository for daily pharma sales records."""

from datetime import date
from typing import List, Optional

from sqlalchemy import text

from app.constants import ATC_COLUMNS
from app.database import postgres_session
from app.schemas import RecordCreate, RecordResponse, RecordUpdate


def _row_to_response(row) -> RecordResponse:
    categories = {col: float(row[col]) for col in ATC_COLUMNS}
    return RecordResponse(
        record_id=row["sale_date"].isoformat(),
        sale_date=row["sale_date"],
        total_demand=float(row["total_demand"]),
        categories=categories,
        sql_record_id=int(row["record_id"]),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _record_filter(record_key: str) -> tuple[str, dict]:
    if record_key.isdigit():
        return "dr.record_id = CAST(:key AS INTEGER)", {"key": record_key}
    return "dr.sale_date = CAST(:key AS DATE)", {"key": record_key}


def _fetch_record(session, record_key: str) -> Optional[RecordResponse]:
    filter_clause, params = _record_filter(record_key)
    query = text(
        f"""
        SELECT
            dr.record_id,
            dr.sale_date,
            dr.total_demand,
            dr.created_at,
            dr.updated_at,
            {", ".join(f"MAX(CASE WHEN cs.medicine_id = '{c}' THEN cs.units_sold END) AS \"{c}\"" for c in ATC_COLUMNS)}
        FROM daily_records dr
        LEFT JOIN category_sales cs ON dr.record_id = cs.record_id
        WHERE {filter_clause}
        GROUP BY dr.record_id, dr.sale_date, dr.total_demand, dr.created_at, dr.updated_at
        """
    )
    row = session.execute(query, params).mappings().first()
    return _row_to_response(row) if row else None


def create_record(payload: RecordCreate) -> RecordResponse:
    total = sum(payload.categories.values())
    with postgres_session() as session:
        existing = session.execute(
            text("SELECT record_id FROM daily_records WHERE sale_date = :sale_date"),
            {"sale_date": payload.sale_date},
        ).first()
        if existing:
            raise ValueError(f"Record already exists for {payload.sale_date}")

        record_id = session.execute(
            text(
                "INSERT INTO daily_records (sale_date, total_demand) "
                "VALUES (:sale_date, :total_demand) "
                "RETURNING record_id"
            ),
            {"sale_date": payload.sale_date, "total_demand": total},
        ).scalar_one()

        for medicine_id, units in payload.categories.items():
            session.execute(
                text(
                    "INSERT INTO category_sales (record_id, medicine_id, units_sold) "
                    "VALUES (:record_id, :medicine_id, :units_sold)"
                ),
                {
                    "record_id": record_id,
                    "medicine_id": medicine_id,
                    "units_sold": units,
                },
            )

        record = _fetch_record(session, str(payload.sale_date))
        if record is None:
            raise RuntimeError("Failed to read back inserted PostgreSQL record")
        return record


def get_record(record_id: str) -> Optional[RecordResponse]:
    with postgres_session() as session:
        return _fetch_record(session, record_id)


def update_record(record_id: str, payload: RecordUpdate) -> Optional[RecordResponse]:
    total = sum(payload.categories.values())
    with postgres_session() as session:
        if record_id.isdigit():
            key_filter = "record_id = CAST(:key AS INTEGER)"
        else:
            key_filter = "sale_date = CAST(:key AS DATE)"

        row = session.execute(
            text(f"SELECT record_id, sale_date FROM daily_records WHERE {key_filter}"),
            {"key": record_id},
        ).mappings().first()
        if not row:
            return None

        pg_id = row["record_id"]
        session.execute(
            text(
                "UPDATE daily_records SET total_demand = :total_demand "
                "WHERE record_id = :record_id"
            ),
            {"total_demand": total, "record_id": pg_id},
        )

        for medicine_id, units in payload.categories.items():
            session.execute(
                text(
                    "UPDATE category_sales SET units_sold = :units_sold "
                    "WHERE record_id = :record_id AND medicine_id = :medicine_id"
                ),
                {
                    "units_sold": units,
                    "record_id": pg_id,
                    "medicine_id": medicine_id,
                },
            )

        return _fetch_record(session, str(row["sale_date"]))


def delete_record(record_id: str) -> bool:
    with postgres_session() as session:
        if record_id.isdigit():
            result = session.execute(
                text("DELETE FROM daily_records WHERE record_id = CAST(:key AS INTEGER)"),
                {"key": record_id},
            )
        else:
            result = session.execute(
                text("DELETE FROM daily_records WHERE sale_date = CAST(:key AS DATE)"),
                {"key": record_id},
            )
        return result.rowcount > 0


def get_latest_record() -> Optional[RecordResponse]:
    with postgres_session() as session:
        row = session.execute(
            text("SELECT sale_date FROM daily_records ORDER BY sale_date DESC LIMIT 1")
        ).first()
        if not row:
            return None
        return _fetch_record(session, row[0].isoformat())


def get_records_by_range(start_date: date, end_date: date) -> List[RecordResponse]:
    with postgres_session() as session:
        dates = session.execute(
            text(
                "SELECT sale_date FROM daily_records "
                "WHERE sale_date BETWEEN :start_date AND :end_date "
                "ORDER BY sale_date"
            ),
            {"start_date": start_date, "end_date": end_date},
        ).scalars().all()

        return [
            record
            for sale_date in dates
            if (record := _fetch_record(session, sale_date.isoformat())) is not None
        ]
