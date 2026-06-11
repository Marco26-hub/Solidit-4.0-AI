from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

KINDS = ("grey_scale", "white_tile", "colour_target", "lightbox", "other")


class LabCoords(BaseModel):
    L: float
    a: float
    b: float


class CalibrationReferenceCreate(BaseModel):
    kind: str = Field(pattern="^(grey_scale|white_tile|colour_target|lightbox|other)$")
    code: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    certificate_number: str | None = Field(default=None, max_length=200)
    valid_from: dt.date | None = None
    valid_until: dt.date | None = None
    # certified CIELAB of a white tile / colour target (anchors in-frame correction)
    reference_values: LabCoords | None = None


class CalibrationReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    code: str
    description: str | None
    certificate_number: str | None
    valid_from: dt.date | None
    valid_until: dt.date | None
    status: str
    reference_values: dict | None = None
    # computed validity: valid | expiring | expired | retired
    validity: str
    created_at: dt.datetime
