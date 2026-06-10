from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    metadata: dict = Field(default_factory=dict)


class DepartmentUpdate(BaseModel):
    name: str | None = None
    metadata: dict | None = None
    is_active: bool | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    code: str
    name: str
    metadata: dict = Field(default_factory=dict, validation_alias="meta")
    is_active: bool
    created_at: datetime
    updated_at: datetime
