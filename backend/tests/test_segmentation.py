from __future__ import annotations

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

import numpy as np  # noqa: E402

from app.vision.quality import assess_capture  # noqa: E402
from app.vision.segmentation import detect_and_split  # noqa: E402

FIBERS = ["a", "b", "c", "d", "e", "f"]
COLORS = [
    (240, 240, 240),
    (235, 238, 240),
    (180, 90, 90),  # stained
    (238, 236, 240),
    (90, 150, 90),  # stained
    (240, 238, 236),
]


def _strip(colors, band_w=50, h=120):
    arr = np.zeros((h, band_w * len(colors), 3), dtype=np.uint8)
    for i, c in enumerate(colors):
        arr[:, i * band_w : (i + 1) * band_w] = c
    return arr


def _mean_rgb(roi):
    return np.asarray(roi, dtype=np.float64).reshape(-1, 3).mean(axis=0)


def test_bands_detected_in_order_full_frame():
    arr = _strip(COLORS)
    seg = detect_and_split(arr, FIBERS)
    assert seg["order"] == FIBERS
    assert seg["orientation"] == "horizontal"
    # each band ROI's mean colour matches the colour painted at that position
    for i, f in enumerate(FIBERS):
        got = _mean_rgb(seg["rois"][f])
        assert np.allclose(got, COLORS[i], atol=12), (f, got, COLORS[i])


def test_strip_autocropped_from_contrasting_background():
    strip = _strip(COLORS, band_w=45, h=100)  # 270 x 100
    # place the strip on a dark dima background with small margins (strip fills
    # most of the frame, as guaranteed in practice by the physical dima)
    canvas = np.full((120, 300, 3), 20, dtype=np.uint8)
    y0, x0 = 10, 15
    canvas[y0 : y0 + strip.shape[0], x0 : x0 + strip.shape[1]] = strip
    seg = detect_and_split(canvas, FIBERS)
    # bbox should be inside the canvas (cropped), not the full frame
    by0, by1, bx0, bx1 = seg["bbox"]
    assert by0 >= 5 and bx0 >= 5
    assert seg["fill_ratio"] < 1.0
    # bands still mapped in order
    for i, f in enumerate(FIBERS):
        got = _mean_rgb(seg["rois"][f])
        assert np.allclose(got, COLORS[i], atol=18), (f, got, COLORS[i])


def test_vertical_strip_orientation():
    arr = np.transpose(_strip(COLORS), (1, 0, 2)).copy()  # tall strip
    seg = detect_and_split(arr, FIBERS)
    assert seg["orientation"] == "vertical"
    assert seg["order"] == FIBERS


def test_quality_flags_blur_and_fill():
    # uniform mid-grey image: no high-frequency content -> blurry/low-detail
    flat = np.full((100, 300, 3), 128, dtype=np.uint8)
    q = assess_capture(flat, fill_ratio=0.05)
    assert q["blur_score"] < 60.0
    assert any("blur" in w for w in q["warnings"])
    assert any("framing" in w for w in q["warnings"])
    assert q["acceptable"] is False
