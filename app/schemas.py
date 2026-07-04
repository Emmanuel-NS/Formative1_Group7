"""Pydantic schemas for API request/response bodies."""

from datetime import date, datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.constants import ATC_COLUMNS


class CategorySales(BaseModel):
    categories: Dict[str, float] = Field(
        ..., description="ATC category code → units sold"
    )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: Dict[str, float]) -> Dict[str, float]:
        unknown = set(value) - set(ATC_COLUMNS)
        if unknown:
            raise ValueError(f"Unknown ATC categories: {sorted(unknown)}")
        return value


class RecordCreate(CategorySales):
    sale_date: date


class RecordUpdate(CategorySales):
    pass


class RecordResponse(BaseModel):
    record_id: str
    sale_date: date
    total_demand: float
    categories: Dict[str, float]
    sql_record_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DualDatabaseResponse(BaseModel):
    message: str
    sql: Optional[RecordResponse] = None
    mongodb: Optional[RecordResponse] = None


class RecordListResponse(BaseModel):
    count: int
    records: list[RecordResponse]
