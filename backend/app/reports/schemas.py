from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_number: str
    test_job_id: uuid.UUID
    sha256_hash: str
    status: str
    created_at: datetime


class ReportVerify(BaseModel):
    report_number: str
    sha256_hash: str
    recomputed_hash: str
    valid: bool
