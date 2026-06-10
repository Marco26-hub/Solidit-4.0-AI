from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    vat_number: str | None
    account_tier: str
    active_departments: dict
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyUpdate(BaseModel):
    name: str | None = None
    vat_number: str | None = None
    settings: dict | None = None
    active_departments: dict | None = None
