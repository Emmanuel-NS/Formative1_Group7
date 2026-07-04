"""MongoDB repository for daily pharma sales records."""

from datetime import date, datetime, timezone
from typing import List, Optional

from app.constants import ATC_COLUMNS
from app.database import get_mongo_collection
from app.schemas import RecordCreate, RecordResponse, RecordUpdate


def _doc_to_response(doc: dict) -> RecordResponse:
    sale_date = doc["sale_date"]
    if isinstance(sale_date, str):
        sale_date = date.fromisoformat(sale_date)

    return RecordResponse(
        record_id=doc["record_id"],
        sale_date=sale_date,
        total_demand=float(doc["total_demand"]),
        categories={k: float(v) for k, v in doc["categories"].items()},
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def create_record(payload: RecordCreate) -> RecordResponse:
    collection = get_mongo_collection()
    record_id = payload.sale_date.isoformat()
    if collection.find_one({"record_id": record_id}):
        raise ValueError(f"Record already exists for {payload.sale_date}")

    now = datetime.now(timezone.utc)
    doc = {
        "record_id": record_id,
        "sale_date": record_id,
        "total_demand": sum(payload.categories.values()),
        "categories": payload.categories,
        "source": "pharma_sales_daily",
        "created_at": now,
        "updated_at": now,
    }
    collection.insert_one(doc)
    return _doc_to_response(doc)


def get_record(record_id: str) -> Optional[RecordResponse]:
    collection = get_mongo_collection()
    doc = collection.find_one({"record_id": record_id})
    if not doc and not record_id.isdigit():
        doc = collection.find_one({"sale_date": record_id})
    return _doc_to_response(doc) if doc else None


def update_record(record_id: str, payload: RecordUpdate) -> Optional[RecordResponse]:
    collection = get_mongo_collection()
    now = datetime.now(timezone.utc)
    result = collection.find_one_and_update(
        {"record_id": record_id},
        {
            "$set": {
                "categories": payload.categories,
                "total_demand": sum(payload.categories.values()),
                "updated_at": now,
            }
        },
        return_document=True,
    )
    return _doc_to_response(result) if result else None


def delete_record(record_id: str) -> bool:
    collection = get_mongo_collection()
    result = collection.delete_one({"record_id": record_id})
    return result.deleted_count > 0


def get_latest_record() -> Optional[RecordResponse]:
    collection = get_mongo_collection()
    doc = collection.find_one(sort=[("sale_date", -1)])
    return _doc_to_response(doc) if doc else None


def get_records_by_range(start_date: date, end_date: date) -> List[RecordResponse]:
    collection = get_mongo_collection()
    cursor = collection.find(
        {"sale_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}
    ).sort("sale_date", 1)
    return [_doc_to_response(doc) for doc in cursor]
