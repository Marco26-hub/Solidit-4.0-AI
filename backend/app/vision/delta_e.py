"""DeltaE CIEDE2000 between sample and reference Lab values (scikit-image)."""

from __future__ import annotations

from collections.abc import Sequence


def compute_delta_e_ciede2000(lab_sample: Sequence[float], lab_reference: Sequence[float]) -> float:
    import numpy as np
    from skimage.color import deltaE_ciede2000

    a = np.asarray(lab_sample, dtype=np.float64).reshape(1, 1, 3)
    b = np.asarray(lab_reference, dtype=np.float64).reshape(1, 1, 3)
    return float(deltaE_ciede2000(a, b)[0, 0])
