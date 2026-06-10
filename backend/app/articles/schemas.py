from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LabRef(BaseModel):
    L: float
    a: float
    b: float


class VariantCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    color_name: str | None = Field(default=None, max_length=200)
    lot_code: str | None = Field(default=None, max_length=100)
    reference_lab: LabRef | None = None


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    article_id: uuid.UUID
    code: str
    color_name: str | None
    lot_code: str | None
    reference_lab: dict | None
    is_active: bool
    created_at: datetime


class ArticleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)
    composition: str | None = Field(default=None, max_length=200)
    brand_specification_id: uuid.UUID | None = None
    variants: list[VariantCreate] = Field(default_factory=list)


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str | None
    composition: str | None
    brand_specification_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    variants: list[VariantOut] = Field(default_factory=list)


class GradingProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    standard_family: str
    assessment_type: str
    thresholds: list
    is_builtin: bool
