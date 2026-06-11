from __future__ import annotations

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

import numpy as np  # noqa: E402

from app.vision.grey_scale import find_neutral_reference, neutral_white_balance  # noqa: E402


def test_find_neutral_reference_picks_bright_neutral_patch():
    # mostly mid-grey image with a bright neutral white block in one corner
    arr = np.full((240, 240, 3), 90, dtype=np.uint8)
    arr[:60, :60] = (250, 249, 251)  # near-neutral white reference
    ref = find_neutral_reference(arr)
    assert ref is not None
    assert min(ref["rgb"]) > 200
    assert ref["chroma"] < 0.06


def test_find_neutral_reference_none_when_saturated():
    # strongly coloured image, no neutral bright patch
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    arr[:, :] = (200, 30, 30)
    assert find_neutral_reference(arr) is None


def test_neutral_white_balance_removes_colour_cast():
    # warm (reddish) cast: a neutral surface reads 210/180/150
    white = [210.0, 180.0, 150.0]
    arr = np.full((40, 40, 3), white, dtype=np.uint8)
    out = neutral_white_balance(arr, white)
    mean = out.reshape(-1, 3).mean(axis=0)
    # after correction the neutral surface is achromatic (channels ~equal)
    assert float(mean.max() - mean.min()) < 6.0
