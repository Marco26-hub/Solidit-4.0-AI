from __future__ import annotations

import hashlib
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.captures.schemas import CaptureSessionCreate
from app.common.errors import AppError, NotFoundError
from app.common.storage import get_storage
from app.db.models import (
    ArticleVariant,
    CaptureSession,
    ImageAsset,
    MeasurementResult,
    MultifiberBatch,
    MultifiberStripProfile,
    TestJob,
    TestMethod,
)
from app.test_jobs.service import _load_rule_dicts, evaluate_pass_fail

_MULTIFIBER_TYPES = ("multifiber_after", "multifiber")
_COLOUR_CHANGE_TYPES = ("colour_change", "fabric_after")
_MAX_REPLICATES = 5  # how many replicate photos we aggregate for repeatability
_REPEATABILITY_TOL = 0.5  # grade deviation across replicates above this -> warning
_STAINING_REQUIRED_REFS = ("lightbox", "grey_scale", "white_tile")
_COLOUR_CHANGE_REQUIRED_REFS = ("lightbox", "white_tile")

logger = structlog.get_logger(__name__)


def _compute_repeatability(visions: list[dict], thresholds: list[dict], grade_fn) -> dict:
    """Aggregate per-fibre ΔE/grade across replicate analyses. Returns mean ΔE
    (grade re-derived from the mean) and the max grade deviation across shots —
    the ISO repeatability indicator. With one shot, deviation is 0."""
    fibers: set[str] = set()
    for v in visions:
        fibers.update(v.get("fibers", {}).keys())

    per_fiber: dict[str, dict] = {}
    max_dev = 0.0
    for f in fibers:
        des = [v["fibers"][f]["delta_e"] for v in visions if f in v.get("fibers", {})]
        grades = [v["fibers"][f]["gray_scale_grade"] for v in visions if f in v.get("fibers", {})]
        if not des:
            continue
        mean_de = round(sum(des) / len(des), 3)
        dev = round(max(grades) - min(grades), 2) if grades else 0.0
        max_dev = max(max_dev, dev)
        per_fiber[f] = {
            "mean_delta_e": mean_de,
            "grade": grade_fn(mean_de, thresholds),
            "replicate_grades": grades,
            "max_dev_grade": dev,
        }
    return {
        "replicates": len(visions),
        "max_deviation_grade": round(max_dev, 2),
        "per_fiber": per_fiber,
    }


async def _get_job(session: AsyncSession, company_id: uuid.UUID, job_id: uuid.UUID) -> TestJob:
    job = (
        await session.execute(
            select(TestJob).where(TestJob.id == job_id, TestJob.company_id == company_id)
        )
    ).scalar_one_or_none()
    if job is None:
        raise NotFoundError("Test job not found")
    return job


async def create_session(
    session: AsyncSession,
    company_id: uuid.UUID,
    operator_id: uuid.UUID,
    data: CaptureSessionCreate,
) -> CaptureSession:
    await _get_job(session, company_id, data.test_job_id)
    cs = CaptureSession(
        company_id=company_id,
        test_job_id=data.test_job_id,
        operator_id=operator_id,
        device_id=data.device_id,
        batch_id=data.batch_id,
        test_method_code=data.test_method_code,
        capture_type=data.capture_type,
        illuminant=data.illuminant,
        lightbox_ref_id=data.lightbox_ref_id,
        grey_scale_ref_id=data.grey_scale_ref_id,
        white_tile_ref_id=data.white_tile_ref_id,
        colour_target_ref_id=data.colour_target_ref_id,
        telemetry={
            "inframe_grey_scale": data.has_inframe_grey_scale,
            "aruco_rectify": data.aruco_rectify,
            "strict_quality": data.strict_quality,
        },
    )
    session.add(cs)
    await session.flush()
    return cs


async def get_session(
    session: AsyncSession, company_id: uuid.UUID, session_id: uuid.UUID
) -> CaptureSession:
    cs = (
        await session.execute(
            select(CaptureSession).where(
                CaptureSession.id == session_id, CaptureSession.company_id == company_id
            )
        )
    ).scalar_one_or_none()
    if cs is None:
        raise NotFoundError("Capture session not found")
    return cs


async def add_image(
    session: AsyncSession,
    company_id: uuid.UUID,
    session_id: uuid.UUID,
    asset_type: str,
    data: bytes,
    filename: str,
    content_type: str | None,
) -> ImageAsset:
    await get_session(session, company_id, session_id)
    if not data:
        raise AppError("File vuoto.", code="empty_file")
    sha = hashlib.sha256(data).hexdigest()
    key = f"captures/{company_id}/{session_id}/{uuid.uuid4().hex}-{filename}"
    get_storage().put(key, data, content_type or "application/octet-stream")
    width = height = None
    try:
        from io import BytesIO

        from PIL import Image

        with Image.open(BytesIO(data)) as im:
            width, height = im.size
    except Exception as exc:  # noqa: BLE001 - image metadata is best-effort
        # do not fail the upload, but do NOT swallow silently — record why
        logger.warning("image_dimensions_unavailable", filename=filename, error=str(exc))
    asset = ImageAsset(
        company_id=company_id,
        capture_session_id=session_id,
        asset_type=asset_type,
        storage_key=key,
        sha256_hash=sha,
        width=width,
        height=height,
    )
    session.add(asset)
    await session.flush()
    return asset


async def list_images(
    session: AsyncSession, company_id: uuid.UUID, session_id: uuid.UUID
) -> list[ImageAsset]:
    await get_session(session, company_id, session_id)
    stmt = (
        select(ImageAsset)
        .where(
            ImageAsset.company_id == company_id,
            ImageAsset.capture_session_id == session_id,
        )
        .order_by(ImageAsset.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())


async def _resolve_fibers(
    session: AsyncSession, batch: MultifiberBatch, reference: dict
) -> tuple[list[str], str]:
    """Return (ordered fibres, source). source='strip_profile' when the order
    comes from the batch's standard strip; 'reference_keys_fallback' when it does
    not — the latter is surfaced as a warning (the band order is not guaranteed)."""
    if batch.strip_profile_code:
        prof = (
            await session.execute(
                select(MultifiberStripProfile).where(
                    MultifiberStripProfile.code == batch.strip_profile_code
                )
            )
        ).scalar_one_or_none()
        if prof and prof.fibers:
            ordered = [f for f in prof.fibers if f in reference]
            if ordered:
                return ordered, "strip_profile"
    return list(reference.keys()), "reference_keys_fallback"


def _norm_grading_family(raw: str | None) -> str:
    """Map a method's standard_family label (e.g. 'ISO 105-E', 'ISO_105', 'AATCC 16')
    to the grading-profile family key (ISO_105 | AATCC | ASTM)."""
    if not raw:
        return "ISO_105"
    r = raw.upper()
    if "AATCC" in r:
        return "AATCC"
    if "ASTM" in r:
        return "ASTM"
    return "ISO_105"


async def _resolve_thresholds(
    session: AsyncSession,
    company_id: uuid.UUID,
    method_code: str,
    assessment_type: str,
) -> tuple[list[dict], str]:
    """Return (thresholds, profile_label). profile_label is the grading profile
    CODE when a validated/configured profile is used, or 'EXAMPLE_DEFAULT' when
    we fall back to the non-validated placeholder table — surfaced as a warning
    so a report never hides that EXAMPLE thresholds produced the grade."""
    from app.articles.service import resolve_grading_profile
    from app.vision.grading import DEFAULT_STAINING_THRESHOLDS

    method = (
        await session.execute(select(TestMethod).where(TestMethod.code == method_code))
    ).scalar_one_or_none()
    family = _norm_grading_family(method.standard_family if method else None)

    profile = await resolve_grading_profile(
        session, company_id, standard_family=family, assessment_type=assessment_type
    )
    if profile is not None:
        label = profile.code + (" (builtin esempio)" if profile.is_builtin else "")
        return list(profile.thresholds), label
    return DEFAULT_STAINING_THRESHOLDS, "EXAMPLE_DEFAULT"


async def _certified_white_lab(
    session: AsyncSession, company_id: uuid.UUID, cs: CaptureSession
) -> list[float] | None:
    """Certified CIELAB of the linked white-tile / grey-scale reference (if it
    carries certified values) — anchors the in-frame correction to the certificate.

    Prefers the true white-tile anchor; only falls back to a grey-scale reference
    that actually carries certified values (grey scales normally do not)."""
    from app.db.models import CalibrationReference

    # white tile is the metrologically correct anchor; grey scale is a fallback
    for rid in (cs.white_tile_ref_id, cs.grey_scale_ref_id):
        if rid is None:
            continue
        ref = (
            await session.execute(
                select(CalibrationReference).where(
                    CalibrationReference.id == rid,
                    CalibrationReference.company_id == company_id,
                )
            )
        ).scalar_one_or_none()
        vals = ref.reference_values if ref else None
        if vals and all(k in vals for k in ("L", "a", "b")):
            return [float(vals["L"]), float(vals["a"]), float(vals["b"])]
    return None


async def _reference_provenance(
    session: AsyncSession,
    company_id: uuid.UUID,
    cs: CaptureSession,
    *,
    required_slots: tuple[str, ...],
) -> tuple[dict, list[str]]:
    """Validate the capture's linked references (raises if any expired/retired)
    and return (provenance, warnings). Vision analysis is hardware-gated: missing
    required kit references block analysis instead of emitting a soft warning."""
    from app.calibration.service import assert_capture_references_valid

    ref_ids = {
        "lightbox": cs.lightbox_ref_id,
        "grey_scale": cs.grey_scale_ref_id,
        "white_tile": cs.white_tile_ref_id,
        "colour_target": cs.colour_target_ref_id,
    }
    provenance = await assert_capture_references_valid(
        session, company_id, ref_ids, required_slots=required_slots
    )
    warnings: list[str] = []
    if any(p["validity"] == "expiring" for p in provenance.values()):
        warnings.append("references: un riferimento è in scadenza")
    return provenance, warnings


async def _analyze_staining(
    session: AsyncSession,
    company_id: uuid.UUID,
    cs: CaptureSession,
) -> MeasurementResult:
    if cs.batch_id is None:
        raise AppError("Sessione senza lotto multifibra (batch).", code="no_batch")

    # ISO 17025 discipline: analysis is blocked unless the required hardware kit
    # references are linked and valid before any image processing starts.
    refs, ref_warnings = await _reference_provenance(
        session, company_id, cs, required_slots=_STAINING_REQUIRED_REFS
    )

    # all replicate photos of the strip (newest first) — repeatability needs >1
    imgs = list(
        (
            await session.execute(
                select(ImageAsset)
                .where(
                    ImageAsset.company_id == company_id,
                    ImageAsset.capture_session_id == cs.id,
                    ImageAsset.asset_type.in_(_MULTIFIBER_TYPES),
                )
                .order_by(ImageAsset.created_at.desc())
                .limit(_MAX_REPLICATES)
            )
        )
        .scalars()
        .all()
    )
    if not imgs:
        raise AppError("Nessuna foto multifibra caricata in questa sessione.", code="no_image")

    batch = (
        await session.execute(
            select(MultifiberBatch).where(
                MultifiberBatch.id == cs.batch_id, MultifiberBatch.company_id == company_id
            )
        )
    ).scalar_one_or_none()
    if batch is None:
        raise NotFoundError("Batch non trovato")

    reference = dict(batch.reference_lab_values or {})
    if not reference:
        raise AppError("Il batch non ha valori Lab di riferimento.", code="no_reference")

    fibers, fiber_source = await _resolve_fibers(session, batch, reference)
    thresholds, grading_profile = await _resolve_thresholds(
        session, company_id, cs.test_method_code or "", "staining"
    )

    from app.vision.grading import map_delta_e_to_grade
    from app.vision.pipeline import analyze_multifiber

    grey = bool((cs.telemetry or {}).get("inframe_grey_scale"))
    geometry_markers = bool((cs.telemetry or {}).get("aruco_rectify"))
    white_lab = await _certified_white_lab(session, company_id, cs) if grey else None
    # newest image is the primary result; the rest provide repeatability
    replicate_visions = [
        analyze_multifiber(
            get_storage().get(im.storage_key),
            fibers,
            reference,
            thresholds=thresholds,
            grey_scale=grey,
            white_reference_lab=white_lab,
            geometry_markers=geometry_markers,
        )
        for im in imgs
    ]
    vision = replicate_visions[0]
    repeatability = _compute_repeatability(replicate_visions, thresholds, map_delta_e_to_grade)
    vision["repeatability"] = repeatability
    # report repeatability-aggregated (mean) values when there is more than one shot
    if repeatability["replicates"] > 1:
        for f, agg in repeatability["per_fiber"].items():
            if f in vision["fibers"]:
                vision["fibers"][f]["delta_e"] = agg["mean_delta_e"]
                vision["fibers"][f]["gray_scale_grade"] = agg["grade"]

    # surface non-validated/fallback decisions instead of hiding them
    extra_warnings = list(ref_warnings)
    _rep_over = repeatability["max_deviation_grade"] > _REPEATABILITY_TOL
    if repeatability["replicates"] > 1 and _rep_over:
        extra_warnings.append(
            f"ripetibilità: scarto {repeatability['max_deviation_grade']} gradi tra repliche "
            f"(oltre tolleranza {_REPEATABILITY_TOL})"
        )
    vision["quality_flags"]["grading_profile"] = grading_profile
    vision["quality_flags"]["fiber_order"] = fiber_source
    if grading_profile == "EXAMPLE_DEFAULT" or "esempio" in grading_profile:
        extra_warnings.append(
            "grading: soglie ESEMPIO non validate (sostituire con profilo licenziato/validato)"
        )
    if fiber_source != "strip_profile":
        extra_warnings.append(
            "fibre: ordine non garantito dal profilo striscia (associa uno standard al lotto)"
        )
    vision["warnings"] = list(vision.get("warnings", [])) + extra_warnings

    # accreditation strict mode: refuse to emit a result on a poor capture
    if (cs.telemetry or {}).get("strict_quality"):
        cap = vision["quality_flags"]["capture"]
        reasons = list(cap["warnings"])
        if grey and not vision["quality_flags"]["grey_scale"]["detected"]:
            reasons.append("grey-scale non rilevata")
        if reasons:
            raise AppError(
                "Cattura rifiutata (qualità insufficiente): " + "; ".join(reasons),
                code="capture_rejected",
            )

    fibers_meas = {
        f: {"delta_e": v["delta_e"], "gray_scale_grade": v["gray_scale_grade"]}
        for f, v in vision["fibers"].items()
    }

    job = await _get_job(session, company_id, cs.test_job_id)
    rules: list[dict] = []
    if job.brand_specification_id is not None:
        rules = await _load_rule_dicts(session, company_id, job.brand_specification_id)
    verdict = evaluate_pass_fail(rules, cs.test_method_code or "", fibers_meas)

    result = MeasurementResult(
        company_id=company_id,
        test_job_id=cs.test_job_id,
        capture_session_id=cs.id,
        algorithm_version=vision["algorithm_version"],
        results={
            "test_method_code": cs.test_method_code,
            "assessment_type": "staining",
            "source": "vision",
            "vision": vision,
            "references": refs,
        },
        pass_fail=verdict,
    )
    session.add(result)
    job.status = (
        "completed"
        if not verdict["evaluated"]
        else ("passed" if verdict["overall_pass"] else "failed")
    )
    await session.flush()
    return result


async def _analyze_colour_change(
    session: AsyncSession,
    company_id: uuid.UUID,
    cs: CaptureSession,
) -> MeasurementResult:
    """Colour-change analysis: compare fabric ROI against article variant reference Lab."""
    # ISO 17025 discipline: colour-change analysis also requires controlled
    # illumination plus a certified white tile before any RGB->Lab conversion.
    refs, ref_warnings = await _reference_provenance(
        session, company_id, cs, required_slots=_COLOUR_CHANGE_REQUIRED_REFS
    )
    job = await _get_job(session, company_id, cs.test_job_id)
    if job.article_variant_id is None:
        raise AppError("Colour-change richiede article_variant_id sul test job.", code="no_variant")

    variant = (
        await session.execute(
            select(ArticleVariant).where(
                ArticleVariant.id == job.article_variant_id,
                ArticleVariant.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if variant is None:
        raise NotFoundError("Variante articolo non trovata")
    if not variant.reference_lab:
        raise AppError(
            "La variante non ha Lab di riferimento per colour-change.", code="no_reference_lab"
        )

    img = (
        await session.execute(
            select(ImageAsset)
            .where(
                ImageAsset.company_id == company_id,
                ImageAsset.capture_session_id == cs.id,
                ImageAsset.asset_type.in_((*_COLOUR_CHANGE_TYPES, "fabric")),
            )
            .order_by(ImageAsset.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if img is None:
        raise AppError("Nessuna foto tessuto caricata in questa sessione.", code="no_image")

    ref = variant.reference_lab  # {"L": ..., "a": ..., "b": ...}
    raw = get_storage().get(img.storage_key)

    from io import BytesIO

    import numpy as np
    from PIL import Image as PILImage

    from app.vision import ALGORITHM_VERSION
    from app.vision.delta_e import compute_delta_e_ciede2000
    from app.vision.grading import map_delta_e_to_grade
    from app.vision.lab import rgb_to_lab

    with PILImage.open(BytesIO(raw)) as im:
        arr = np.array(im.convert("RGB"))

    # central 50% crop as measurement ROI
    h, w = arr.shape[:2]
    roi = arr[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]

    sample_lab = rgb_to_lab(roi)
    ref_lab = [float(ref["L"]), float(ref["a"]), float(ref["b"])]
    thresholds, grading_profile = await _resolve_thresholds(
        session, company_id, cs.test_method_code or "", "change"
    )

    delta_e = compute_delta_e_ciede2000(sample_lab, ref_lab)
    grade = map_delta_e_to_grade(delta_e, thresholds)

    cc_warnings = list(ref_warnings)
    # colour-change runs on raw RGB with no device colour-correction — surface it
    cc_warnings.append(
        "colour_correction: non applicata (RGB camera grezzo, nessuna taratura device)"
    )
    if grading_profile == "EXAMPLE_DEFAULT" or "esempio" in grading_profile:
        cc_warnings.append("grading: soglie ESEMPIO non validate")

    vision_result = {
        "algorithm_version": ALGORITHM_VERSION,
        "sample_lab": {
            "L": round(sample_lab[0], 2),
            "a": round(sample_lab[1], 2),
            "b": round(sample_lab[2], 2),
        },
        "reference_lab": ref,
        "delta_e": round(delta_e, 3),
        "gray_scale_grade": grade,
        "quality_flags": {
            "roi": "central_50pct",
            "geometry": "assumed-canonical",
            "colour_correction": "none",
            "grading_profile": grading_profile,
        },
        "warnings": cc_warnings,
    }

    fibers_meas = {"fabric": {"delta_e": delta_e, "gray_scale_grade": grade}}
    rules: list[dict] = []
    if job.brand_specification_id is not None:
        rules = await _load_rule_dicts(session, company_id, job.brand_specification_id)
    verdict = evaluate_pass_fail(rules, cs.test_method_code or "", fibers_meas)

    result = MeasurementResult(
        company_id=company_id,
        test_job_id=cs.test_job_id,
        capture_session_id=cs.id,
        algorithm_version=ALGORITHM_VERSION,
        results={
            "test_method_code": cs.test_method_code,
            "assessment_type": "change",
            "source": "vision",
            "vision": vision_result,
            "article_variant_id": str(job.article_variant_id),
            "references": refs,
        },
        pass_fail=verdict,
    )
    session.add(result)
    job.status = (
        "completed"
        if not verdict["evaluated"]
        else ("passed" if verdict["overall_pass"] else "failed")
    )
    await session.flush()
    return result


async def analyze(
    session: AsyncSession,
    company_id: uuid.UUID,
    session_id: uuid.UUID,
    operator_user_id: uuid.UUID | None = None,
) -> MeasurementResult:
    cs = await get_session(session, company_id, session_id)
    if not cs.test_method_code:
        raise AppError("Sessione senza metodo (solidità).", code="no_method")

    if cs.capture_type in _COLOUR_CHANGE_TYPES:
        result = await _analyze_colour_change(session, company_id, cs)
    else:
        result = await _analyze_staining(session, company_id, cs)

    # ISO 17025 §6.2: bind the result to the operator and record whether they
    # hold a registered authorisation for the method. Missing authorisation is a
    # FLAGGED warning (rule 6); in strict mode the capture is refused upfront.
    operator = operator_user_id or cs.operator_id
    result.operator_user_id = operator
    if operator is not None:
        from app.companies.service import check_operator_authorization

        ok, detail = await check_operator_authorization(
            session, company_id, operator, cs.test_method_code
        )
        res = dict(result.results or {})
        res["operator"] = {"user_id": str(operator), "authorized": ok, "detail": detail}
        if not ok:
            vision = res.get("vision")
            if isinstance(vision, dict):
                vision["warnings"] = [*vision.get("warnings", []), detail]
            if (cs.telemetry or {}).get("strict_quality"):
                raise AppError(
                    f"Analisi rifiutata (modalità severa): {detail}",
                    code="operator_not_authorized",
                )
        result.results = res
        await session.flush()
    return result
