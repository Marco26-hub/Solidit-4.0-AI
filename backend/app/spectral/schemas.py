from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

# Only these are supported by the engine; pinning them rejects bad input as 422
# instead of letting a ValueError bubble up as a 500.
Illuminant = Literal["D65", "A"]
Observer = Literal["2"]


class LabInput(BaseModel):
    L: float = Field(ge=0, le=100)
    a: float = Field(ge=-128, le=128)
    b: float = Field(ge=-128, le=128)


class EstimateRequest(BaseModel):
    lab: LabInput
    illuminant: Illuminant = "D65"
    observer: Observer = "2"


class ReflectanceEstimate(BaseModel):
    estimate: bool = True
    not_a_measurement: bool = True
    label: str
    method: str
    engine: str
    illuminant: str
    observer: str
    wavelengths_nm: list[int]
    reflectance: list[float]
    input_lab: list[float]
    roundtrip_lab: list[float]
    roundtrip_delta_e: float
    confidence: float
    warnings: list[str]
    disclaimer: str


class RenderRequest(BaseModel):
    reflectance: list[Annotated[float, Field(ge=0.0, le=1.0)]] = Field(
        min_length=31, max_length=31
    )
    illuminant: Illuminant = "A"
    observer: Observer = "2"


class RenderResult(BaseModel):
    estimate: bool = True
    not_a_measurement: bool = True
    label: str
    illuminant: str
    observer: str
    lab: list[float]
    srgb: list[int]
    disclaimer: str


class FiberEstimate(BaseModel):
    fiber: str
    sample_lab: list[float]
    estimate: ReflectanceEstimate


class ResultSpectralOut(BaseModel):
    measurement_result_id: str
    label: str
    disclaimer: str
    note: str
    fibers: list[FiberEstimate]
