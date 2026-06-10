from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AcceptanceRuleIn(BaseModel):
    test_method_code: str = Field(min_length=1, max_length=100)
    fiber_code: str | None = Field(default=None, max_length=50)
    max_delta_e: float | None = Field(default=None, ge=0)
    min_gray_scale_grade: float | None = Field(default=None, ge=1, le=5)
    severity: str = Field(default="blocking", pattern="^(blocking|warning)$")
    rule_payload: dict = Field(default_factory=dict)


class AcceptanceRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_method_code: str
    fiber_code: str | None
    max_delta_e: float | None
    min_gray_scale_grade: float | None
    severity: str
    is_active: bool


class BrandSpecCreate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    rules: list[AcceptanceRuleIn] = Field(default_factory=list)


class BrandSpecImport(BaseModel):
    """Create a brand spec from a pasted capitolato rules table (CSV)."""

    brand_name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    rules_csv: str = Field(min_length=1)


class BrandSpecOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    brand_name: str
    description: str | None
    metadata: dict = Field(default_factory=dict, validation_alias="meta")
    is_active: bool
    created_at: datetime
    rules: list[AcceptanceRuleOut] = Field(default_factory=list)
