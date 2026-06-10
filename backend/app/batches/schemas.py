from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LabValue(BaseModel):
    L: float
    a: float
    b: float


class StripProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    standard_family: str | None
    fibers: list[str]


class BatchCreate(BaseModel):
    batch_code: str = Field(min_length=1, max_length=100)
    supplier: str | None = Field(default=None, max_length=200)
    # multifiber strip standard (AATCC / ISO 105-F10 DW/TV …); fibres follow it
    strip_profile_code: str | None = Field(default=None, max_length=80)
    opened_at: datetime | None = None
    expires_at: datetime | None = None
    # reference Lab values per fiber, e.g. {"cotton": {"L":96,"a":0.1,"b":0.9}, ...}
    reference_lab_values: dict[str, LabValue]


class BatchStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|exhausted|expired|retired)$")


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_code: str
    supplier: str | None
    strip_profile_code: str | None
    opened_at: datetime | None
    expires_at: datetime | None
    reference_lab_values: dict
    status: str
    created_at: datetime
