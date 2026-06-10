from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegister(BaseModel):
    hardware_uuid: str = Field(min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=120)
    os_version: str | None = Field(default=None, max_length=60)
    mdm_managed: bool = False
    name: str | None = Field(default=None, min_length=1, max_length=200)  # else model/hw_uuid


class CalibrationUpload(BaseModel):
    illuminant: Literal["D65", "TL84"]
    # 3x3 color-correction matrix (rows of 3) computed from the reference card.
    matrix: list[list[float]]
    profile: dict = Field(default_factory=dict)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    hardware_uuid: str
    model: str | None
    os_version: str | None
    mdm_managed: bool
    calibration_profile: dict
    active_d65_matrix: dict | None
    active_tl84_matrix: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
