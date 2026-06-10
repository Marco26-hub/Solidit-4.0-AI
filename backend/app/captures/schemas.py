from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CaptureSessionCreate(BaseModel):
    test_job_id: uuid.UUID
    capture_type: str = Field(default="multifiber_after", max_length=50)
    illuminant: str | None = Field(default=None, max_length=20)
    batch_id: uuid.UUID | None = None  # the multifiber lot used
    test_method_code: str | None = Field(default=None, max_length=100)  # which solidità
    device_id: uuid.UUID | None = None
    # physical references/instruments used (validity enforced at analyze)
    lightbox_ref_id: uuid.UUID | None = None
    grey_scale_ref_id: uuid.UUID | None = None
    white_tile_ref_id: uuid.UUID | None = None
    colour_target_ref_id: uuid.UUID | None = None


class CaptureSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_job_id: uuid.UUID
    capture_type: str
    illuminant: str | None
    batch_id: uuid.UUID | None
    test_method_code: str | None
    validation_status: str
    created_at: datetime


class ImageAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_type: str
    storage_key: str
    sha256_hash: str
    width: int | None
    height: int | None
    created_at: datetime
