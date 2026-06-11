from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProficiencyTestCreate(BaseModel):
    scheme: str = Field(min_length=1, max_length=200)
    round_label: str = Field(min_length=1, max_length=100)
    parameter: str | None = Field(default=None, max_length=200)
    test_method_code: str | None = Field(default=None, max_length=100)
    result_x: float
    assigned_value: float
    std_dev: float | None = Field(default=None, gt=0)  # SDPA (sigma) for z-score
    u_lab: float | None = Field(default=None, ge=0)  # for En
    u_ref: float | None = Field(default=None, ge=0)
    test_date: dt.date | None = None


class ProficiencyTestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme: str
    round_label: str
    parameter: str | None
    test_method_code: str | None
    result_x: float
    assigned_value: float
    std_dev: float | None
    u_lab: float | None
    u_ref: float | None
    z_score: float | None
    en_number: float | None
    verdict: str
    test_date: dt.date | None
    created_at: dt.datetime
