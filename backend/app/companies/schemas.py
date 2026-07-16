from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


# ── Team members ──────────────────────────────────────────────────────────────
MemberRole = Literal["operator", "lab_manager", "company_admin"]


class MemberCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    # temporary password the admin hands to the member (they should change it)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)
    role: MemberRole = "operator"


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    created_at: datetime


# ── Operator authorizations (ISO 17025 §6.2) ─────────────────────────────────


class AuthorizationCreate(BaseModel):
    user_id: uuid.UUID
    # NULL = authorised for all methods (general authorisation)
    method_code: str | None = Field(default=None, max_length=100)
    valid_until: date | None = None
    training_notes: str | None = Field(default=None, max_length=2000)


class AuthorizationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    method_code: str | None
    valid_from: date
    valid_until: date | None
    training_notes: str | None
    status: str
