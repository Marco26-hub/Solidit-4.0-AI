# VISION_ENGINE_SPEC.md — Solidità 4.0

## Obiettivo

Implementare un motore di analisi immagine per supportare:
- acquisizione multifibra;
- crocking cloth;
- cambio colore;
- staining;
- DeltaE CIEDE2000;
- grey scale mapping configurabile;
- pass/fail secondo brand rules.

## Errore da evitare

L'omografia non neutralizza la luce.

Corretto:
- omografia = correzione geometrica;
- calibrazione colore = matrice colore/LUT/profilo camera usando tile/reference card;
- lightbox = controllo fisico dell'illuminante.

## Pipeline

```
Raw RGB Image
  -> capture validation
  -> marker detection
  -> homography
  -> crop canonical layout
  -> color correction
  -> ROI segmentation
  -> RGB to Lab
  -> DeltaE CIEDE2000
  -> grey scale mapping
  -> brand rule evaluation
  -> persistence
```

## Funzioni principali

### validate_capture(image, telemetry)

Controlli:
- blur;
- esposizione;
- marker visibili;
- tile visibile;
- ROI completa;
- distanza coerente;
- device stabile;
- illuminante selezionato.

### detect_markers(image)

Usa ArUco/AprilTag per trovare punti noti.

### rectify_perspective(image, marker_points)

Applica omografia e genera immagine canonica.

### compute_color_correction(image, reference_patches)

Calcola:
- white balance;
- matrice 3x3;
- optional LUT.

### extract_multifiber_rois(image)

Restituisce ROI per:
- acetate;
- cotton;
- nylon;
- polyester;
- acrylic;
- wool.

### rgb_to_lab(rgb)

Conversione standard.

### compute_delta_e_ciede2000(lab_sample, lab_reference)

Calcola DeltaE CIEDE2000.

### map_delta_e_to_gray_scale(delta_e, standard_profile)

Motore configurabile.

Non hardcodare formule ISO/AATCC proprietarie. Usare profili configurabili:

```json
{
  "profile_name": "ISO_105_A05_INTERNAL_VALIDATED",
  "coefficients": {},
  "thresholds": [
    {"max_delta_e": 0.2, "grade": 5.0},
    {"max_delta_e": 0.8, "grade": 4.5},
    {"max_delta_e": 1.5, "grade": 4.0}
  ]
}
```

## Esempio codice Python

```python
import cv2
import numpy as np
from skimage import color
from skimage.color import deltaE_ciede2000

def rectify_perspective(image_bgr: np.ndarray, src_points: np.ndarray, output_size=(1200, 800)) -> np.ndarray:
    dst_points = np.array([
        [0, 0],
        [output_size[0] - 1, 0],
        [output_size[0] - 1, output_size[1] - 1],
        [0, output_size[1] - 1],
    ], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src_points.astype(np.float32), dst_points)
    return cv2.warpPerspective(image_bgr, matrix, output_size)

def apply_color_matrix(image_rgb: np.ndarray, matrix_3x3: np.ndarray) -> np.ndarray:
    img = image_rgb.astype(np.float32) / 255.0
    corrected = img @ matrix_3x3.T
    corrected = np.clip(corrected, 0, 1)
    return (corrected * 255).astype(np.uint8)

def rgb_patch_to_lab(rgb_patch: np.ndarray) -> np.ndarray:
    rgb = rgb_patch.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb)
    return np.mean(lab.reshape(-1, 3), axis=0)

def compute_delta_e(sample_lab: np.ndarray, reference_lab: np.ndarray) -> float:
    sample = np.array([[sample_lab]], dtype=np.float64)
    reference = np.array([[reference_lab]], dtype=np.float64)
    return float(deltaE_ciede2000(sample, reference)[0, 0])

def map_delta_e_to_grade(delta_e: float, thresholds: list[dict]) -> float:
    sorted_thresholds = sorted(thresholds, key=lambda x: x["max_delta_e"])
    for row in sorted_thresholds:
        if delta_e <= row["max_delta_e"]:
            return float(row["grade"])
    return 1.0
```

## Quality flags

Ogni risultato deve includere:
- confidence;
- capture_quality_score;
- calibration_profile_id;
- algorithm_version;
- warning list.

## Output risultato esempio

```json
{
  "algorithm_version": "vision-core-0.1.0",
  "illuminant": "D65",
  "fibers": {
    "cotton": {
      "sample_lab": {"L": 92.1, "a": 0.5, "b": 2.2},
      "reference_lab": {"L": 96.0, "a": 0.1, "b": 0.9},
      "delta_e_00": 2.15,
      "gray_scale_grade": 3.5,
      "pass": false
    }
  },
  "quality_flags": {
    "blur_score": 0.91,
    "exposure_ok": true,
    "geometry_ok": true
  }
}
```
