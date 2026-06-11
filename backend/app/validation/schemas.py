from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ValidationRunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ValidationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str | None = None
    status: str
    metrics: dict
    created_at: dt.datetime


class ValidationSampleCreate(BaseModel):
    sample_code: str = Field(min_length=1, max_length=100)
    fiber: str | None = Field(default=None, max_length=60)
    reference_method: str = Field(
        default="spectrophotometer",
        pattern="^(spectrophotometer|visual|external_lab)$",
    )
    software_grade: float | None = Field(default=None, ge=1, le=5)
    reference_grade: float | None = Field(default=None, ge=1, le=5)
    software_delta_e: float | None = Field(default=None, ge=0)
    reference_delta_e: float | None = Field(default=None, ge=0)


class ValidationSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sample_code: str
    fiber: str | None
    reference_method: str
    software_grade: float | None
    reference_grade: float | None
    software_delta_e: float | None
    reference_delta_e: float | None


class ValidationRunDetail(ValidationRunOut):
    samples: list[ValidationSampleOut] = Field(default_factory=list)
