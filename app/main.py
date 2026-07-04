"""FastAPI application — CRUD + time-series endpoints for PostgreSQL and MongoDB (Task 3)."""

from datetime import date

from fastapi import FastAPI, HTTPException, Query

from app.database import ping_mongodb, ping_postgres
from app.repositories import mongo_repo, postgres_repo
from app.schemas import (
    DualDatabaseResponse,
    RecordCreate,
    RecordListResponse,
    RecordUpdate,
)

app = FastAPI(
    title="Pharma Time-Series API",
    description="CRUD and time-series query endpoints backed by PostgreSQL and MongoDB.",
    version="1.0.0",
)


def _dual_create(payload: RecordCreate) -> DualDatabaseResponse:
    try:
        sql_record = postgres_repo.create_record(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=f"PostgreSQL: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PostgreSQL error: {exc}") from exc

    try:
        mongo_record = mongo_repo.create_record(payload)
    except ValueError as exc:
        postgres_repo.delete_record(payload.sale_date.isoformat())
        raise HTTPException(status_code=409, detail=f"MongoDB: {exc}") from exc
    except Exception as exc:
        postgres_repo.delete_record(payload.sale_date.isoformat())
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}") from exc

    return DualDatabaseResponse(
        message="Record created in PostgreSQL and MongoDB",
        sql=sql_record,
        mongodb=mongo_record,
    )


@app.get("/health")
def health_check():
    """Verify API and database connectivity."""
    status = {"api": "ok", "postgres": "unknown", "mongodb": "unknown"}
    try:
        ping_postgres()
        status["postgres"] = "ok"
    except Exception as exc:
        status["postgres"] = f"error: {exc}"

    try:
        ping_mongodb()
        status["mongodb"] = "ok"
    except Exception as exc:
        status["mongodb"] = f"error: {exc}"

    return status


@app.post("/api/records", response_model=DualDatabaseResponse, status_code=201)
def create_record(payload: RecordCreate):
    """Insert a new daily sales record into both PostgreSQL and MongoDB."""
    return _dual_create(payload)


@app.get("/api/records/latest", response_model=RecordListResponse)
def get_latest_records():
    """Return the latest record from both databases."""
    sql_record = postgres_repo.get_latest_record()
    mongo_record = mongo_repo.get_latest_record()

    records = []
    if sql_record:
        records.append(sql_record)
    if mongo_record and all(r.record_id != mongo_record.record_id for r in records):
        records.append(mongo_record)

    if not records:
        raise HTTPException(status_code=404, detail="No records found")

    return RecordListResponse(count=len(records), records=records)


@app.get("/api/records/range", response_model=RecordListResponse)
def get_records_by_range(
    start_date: date = Query(..., description="Inclusive start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Inclusive end date (YYYY-MM-DD)"),
    source: str = Query("sql", pattern="^(sql|mongo|both)$"),
):
    """Query records within a date range from PostgreSQL, MongoDB, or both."""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    records = []

    if source in ("sql", "both"):
        records.extend(postgres_repo.get_records_by_range(start_date, end_date))

    if source in ("mongo", "both"):
        mongo_records = mongo_repo.get_records_by_range(start_date, end_date)
        if source == "mongo":
            records = mongo_records
        else:
            existing_ids = {r.record_id for r in records}
            records.extend(r for r in mongo_records if r.record_id not in existing_ids)

    if not records:
        raise HTTPException(status_code=404, detail="No records in date range")

    return RecordListResponse(count=len(records), records=records)


@app.get("/api/records/{record_id}", response_model=DualDatabaseResponse)
def get_record(record_id: str):
    """Fetch a single record from both databases."""
    sql_record = postgres_repo.get_record(record_id)
    mongo_record = mongo_repo.get_record(record_id)

    if not sql_record and not mongo_record:
        raise HTTPException(status_code=404, detail="Record not found")

    return DualDatabaseResponse(
        message="Record fetched from available databases",
        sql=sql_record,
        mongodb=mongo_record,
    )


@app.put("/api/records/{record_id}", response_model=DualDatabaseResponse)
def update_record(record_id: str, payload: RecordUpdate):
    """Update a record in both PostgreSQL and MongoDB."""
    sql_record = postgres_repo.update_record(record_id, payload)
    mongo_record = mongo_repo.update_record(record_id, payload)

    if not sql_record and not mongo_record:
        raise HTTPException(status_code=404, detail="Record not found")

    return DualDatabaseResponse(
        message="Record updated in available databases",
        sql=sql_record,
        mongodb=mongo_record,
    )


@app.delete("/api/records/{record_id}", response_model=DualDatabaseResponse)
def delete_record(record_id: str):
    """Delete a record from both PostgreSQL and MongoDB."""
    sql_deleted = postgres_repo.delete_record(record_id)
    mongo_deleted = mongo_repo.delete_record(record_id)

    if not sql_deleted and not mongo_deleted:
        raise HTTPException(status_code=404, detail="Record not found")

    return DualDatabaseResponse(
        message=f"PostgreSQL deleted={sql_deleted}, MongoDB deleted={mongo_deleted}",
        sql=None,
        mongodb=None,
    )
