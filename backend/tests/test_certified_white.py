from __future__ import annotations

from io import BytesIO

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from app.vision.grey_scale import lab_to_rgb255, white_balance_to_certified  # noqa: E402
from app.vision.pipeline import analyze_multifiber  # noqa: E402


def test_lab_to_rgb_white_is_white():
    rgb = lab_to_rgb255([100.0, 0.0, 0.0])  # L*=100 -> white
    assert min(rgb) > 245


def test_certified_white_balance_anchors_to_target():
    # measured neutral patch reads dim/warm 200/170/150; certified white L*=95
    arr = np.full((20, 20, 3), [200, 170, 150], dtype=np.uint8)
    out = white_balance_to_certified(arr, [200.0, 170.0, 150.0], [95.0, 0.0, 0.0])
    mean = out.reshape(-1, 3).mean(axis=0)
    target = lab_to_rgb255([95.0, 0.0, 0.0])
    # corrected patch lands near the certified white's sRGB (within clamp)
    assert float(np.abs(mean - np.asarray(target)).mean()) < 20.0


def _strip_with_white(stain):
    # 6 fibre bands + a neutral white reference block in the corner
    cols = [(245, 245, 245)] * 5 + [stain]
    arr = np.zeros((120, 360, 3), dtype=np.uint8)
    for i, c in enumerate(cols):
        arr[:, i * 60 : (i + 1) * 60] = c
    arr[:30, :40] = (250, 249, 251)  # bright neutral reference patch
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def test_pipeline_uses_certified_white_flag():
    fibers = ["a", "b", "c", "d", "e", "f"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    png = _strip_with_white((170, 80, 80))
    out = analyze_multifiber(
        png, fibers, ref, grey_scale=True, white_reference_lab=[95.0, 0.0, 0.0]
    )
    assert out["quality_flags"]["colour_correction"] == "in_frame_certified_white"
    assert out["quality_flags"]["grey_scale"]["detected"] is True
    assert out["quality_flags"]["grey_scale"]["certified_lab"] == [95.0, 0.0, 0.0]
