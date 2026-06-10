from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Bootstrap a new tenant: creates the user, the company and an owner
    membership in one transaction."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    company_name: str = Field(min_length=1, max_length=200)
    vat_number: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    company_id: uuid.UUID | None = None  # optional tenant pre-selection


class RefreshRequest(BaseModel):
    refresh_token: str
    company_id: uuid.UUID | None = None


class LogoutRequest(BaseModel):
    refresh_token: str


class SelectCompanyRequest(BaseModel):
    company_id: uuid.UUID


class CompanyBrief(BaseModel):
    id: uuid.UUID
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    company_id: uuid.UUID | None = None
    role: str | None = None
    companies: list[CompanyBrief] = []
