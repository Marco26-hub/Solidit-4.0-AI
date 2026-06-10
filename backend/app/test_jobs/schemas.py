from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TestJobCreate(BaseModel):
    department_id: uuid.UUID | None = None
    brand_specification_id: uuid.UUID | None = None
    test_method_code: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=200)
    article_code: str | None = Field(default=None, max_length=200)
    lot_code: str | None = Field(default=None, max_length=200)
    # production-sample reference (article + colorway variant) for colour-change
    article_id: uuid.UUID | None = None
    article_variant_id: uuid.UUID | None = None
    metadata: dict = Field(default_factory=dict)


class TestJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    department_id: uuid.UUID | None
    brand_specification_id: uuid.UUID | None
    test_method_id: uuid.UUID | None
    barcode: str | None
    article_code: str | None
    lot_code: str | None
    article_id: uuid.UUID | None
    article_variant_id: uuid.UUID | None
    status: str
    metadata: dict = Field(default_factory=dict, validation_alias="meta")
    created_at: datetime


class FiberMeasurement(BaseModel):
    delta_e: float | None = Field(default=None, ge=0)
    gray_scale_grade: float | None = Field(default=None, ge=1, le=5)


class ManualResultCreate(BaseModel):
    """Operator/lab manager enters measured values manually (Trace, no Vision)."""

    test_method_code: str = Field(min_length=1, max_length=100)
    fibers: dict[str, FiberMeasurement] = Field(min_length=1)
    notes: str | None = None


class MeasurementResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    algorithm_version: str
    results: dict
    pass_fail: dict
    created_at: datetime
