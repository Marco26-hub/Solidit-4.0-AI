"""Shared response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
