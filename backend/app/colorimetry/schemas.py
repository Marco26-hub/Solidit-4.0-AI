from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

Degree = Literal[1, 2, 3]
RgbTriple = Annotated[list[float], Field(min_length=3, max_length=3)]


class CharacterizeRequest(BaseModel):
    # measured LINEAR camera RGB (RAW/ProRAW-linearised) of the ColorChecker
    # patches, in capture order. 0..1 or 0..255 accepted.
    patches: list[RgbTriple] = Field(min_length=6, max_length=140)
    degree: Degree = 2
    # optional custom reference CIELAB per patch (defaults to ColorChecker24 D65)
    reference_lab: list[RgbTriple] | None = None


class PatchResidual(BaseModel):
    patch: int
    delta_e: float


class ResidualBudget(BaseModel):
    mean_delta_e: float
    max_delta_e: float
    rms_delta_e: float
    p95_delta_e: float


class CharacterizeResponse(BaseModel):
    method: str
    degree: int
    n_terms: int
    n_patches: int
    reference: str
    matrix: list[list[float]]
    residual: ResidualBudget
    per_patch: list[PatchResidual]


class ApplyRequest(BaseModel):
    matrix: list[list[float]]
    rgb: RgbTriple
    degree: Degree = 2


class ApplyResponse(BaseModel):
    xyz: list[float]
    lab: list[float]


class UncertaintyComponentInput(BaseModel):
    component: str = Field(min_length=1, max_length=80)
    value: float | None = Field(default=None, ge=0)
    input_type: Literal[
        "standard_uncertainty",
        "expanded_uncertainty",
        "half_width",
        "standard_deviation",
    ] = "standard_uncertainty"
    distribution: Literal["normal", "rectangular", "triangular", "u_shaped"] = "normal"
    coverage_factor: float | None = Field(default=None, gt=0)
    degrees_freedom: float | None = Field(default=None, gt=0)
    n: int | None = Field(default=None, ge=2)
    use_mean: bool = True
    observations: list[float] | None = None


class UncertaintyRequest(BaseModel):
    # Simple form: values are already standard uncertainties in DeltaE units.
    repeatability: float | None = Field(default=None, ge=0)
    characterisation: float | None = Field(default=None, ge=0)
    reproducibility: float | None = Field(default=None, ge=0)
    reference: float | None = Field(default=None, ge=0)
    # Advanced form: Type A/Type B components. When present, this overrides the
    # simple fields above.
    components: list[UncertaintyComponentInput] | None = None
    coverage_factor: float | None = Field(default=2.0, gt=0)
    confidence_level: float = Field(default=0.95, gt=0.5, lt=1)
    measured_value: float | None = Field(default=None, ge=0)
    tolerance_limit: float | None = Field(default=None, ge=0)
    decision_direction: Literal["max", "min"] = "max"


class UncertaintyComponent(BaseModel):
    component: str
    standard_uncertainty: float
    distribution: str | None = None
    source: str | None = None
    degrees_freedom: float | None = None
    variance_share_pct: float


class DecisionRule(BaseModel):
    rule: str
    direction: str
    measured_value: float
    tolerance_limit: float
    guard_band: float
    verdict: str


class UncertaintyResponse(BaseModel):
    unit: str
    components: list[UncertaintyComponent]
    combined_standard_uncertainty: float
    effective_degrees_freedom: float | None
    coverage_factor: float
    coverage_method: str
    expanded_uncertainty: float
    confidence_level: str | None
    decision_rule: DecisionRule | None
    dominant_component: str | None
    note: str
