from __future__ import annotations

import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

KINDS = ("grey_scale", "white_tile", "colour_target", "blue_wool", "lightbox", "other")
_KIND_PATTERN = "^(grey_scale|white_tile|colour_target|blue_wool|lightbox|other)$"


class LabCoords(BaseModel):
    L: float
    a: float
    b: float


class PatchLab(BaseModel):
    """One certified patch of a multi-patch colour target (e.g. ColorChecker)."""

    patch_id: str = Field(min_length=1, max_length=50)
    L: float
    a: float
    b: float


class CalibrationReferenceCreate(BaseModel):
    kind: str = Field(pattern=_KIND_PATTERN)
    code: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    certificate_number: str | None = Field(default=None, max_length=200)
    valid_from: dt.date | None = None
    valid_until: dt.date | None = None
    # certified CIELAB of a white tile (anchors in-frame colour correction)
    reference_values: LabCoords | None = None

    # ── optional descriptive attributes (stored in the meta JSONB; all nullable
    #    so existing clients keep working). PUBLIC identifiers only — never the
    #    copyrighted standard text. ───────────────────────────────────────────
    # grey scale: A03 = staining/scarico · A02 = colour change/degradazione
    subtype: Literal["A02", "A03"] | None = None
    # blue wool numbering series
    series: Literal["iso_1_8", "aatcc_l2_l9"] | None = None
    # public standard label, e.g. "ISO 105-B02"
    standard: str | None = Field(default=None, max_length=100)
    # light box: installed illuminants (D65, TL84, UV, A, CWF, …)
    illuminants: list[str] | None = None
    lamp_hours: float | None = None
    # certificate viewing conditions for anchors (e.g. "D65", "10°")
    cert_illuminant: str | None = Field(default=None, max_length=40)
    cert_observer: str | None = Field(default=None, max_length=40)
    # consumable bucket (multifibre / crock_cloth / perspiration / detergent / …)
    consumable_type: str | None = Field(default=None, max_length=60)
    # multi-patch colour target certified values
    patch_values: list[PatchLab] | None = None


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

    # descriptive attributes re-expanded from meta (nullable)
    subtype: str | None = None
    series: str | None = None
    standard: str | None = None
    illuminants: list[str] | None = None
    lamp_hours: float | None = None
    cert_illuminant: str | None = None
    cert_observer: str | None = None
    consumable_type: str | None = None
    patch_values: list[dict] | None = None
