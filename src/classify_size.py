"""
Size classification for LPG cylinders.

Two approaches, used together:

1. Visual classification (the YOLO model itself).
   Train separate classes for each size. Works well when sizes look different
   (20lb is short and fat, 100lb is tall). Needs enough training images of
   each size.

2. Height-ratio estimation (backup and validation).
   If the camera is fixed and calibrated, the pixel height of a detected
   cylinder maps to a real-world height. Compare against known sizes:
     20lb  ~ 46 cm
     30lb  ~ 61 cm
     100lb ~ 122 cm

   This catches cases where the model is uncertain, and it's a useful
   sanity check even when the model is confident.

Calibration: place one cylinder of known size at a known distance, measure
its pixel height, and compute pixels_per_cm. This only needs to be done
once per camera position.
"""

KNOWN_SIZES = {
    "20lb":  46,   # cm
    "30lb":  61,
    "100lb": 122,
}


def calibrate(known_height_cm: float, pixel_height: int) -> float:
    """Returns pixels_per_cm for this camera setup."""
    if pixel_height <= 0:
        raise ValueError("pixel_height must be positive")
    return pixel_height / known_height_cm


def classify_by_height(pixel_height: int, pixels_per_cm: float, tolerance_cm: float = 8.0) -> str | None:
    """Returns the closest matching size label, or None if nothing is close enough."""
    if pixels_per_cm <= 0:
        return None
    real_cm = pixel_height / pixels_per_cm
    best_label = None
    best_diff = float("inf")
    for label, h in KNOWN_SIZES.items():
        diff = abs(real_cm - h)
        if diff < best_diff:
            best_diff = diff
            best_label = label
    return best_label if best_diff <= tolerance_cm else None


def validate_classification(model_class: str, pixel_height: int, pixels_per_cm: float, tolerance_cm: float = 12.0) -> dict:
    """Cross-check the model's classification against the height estimate.
    Returns a dict with the model's call, the height estimate, and whether they agree."""
    height_class = classify_by_height(pixel_height, pixels_per_cm, tolerance_cm)
    return {
        "model_says": model_class,
        "height_says": height_class,
        "agree": model_class == height_class or height_class is None,
        "estimated_cm": round(pixel_height / pixels_per_cm, 1) if pixels_per_cm > 0 else None,
    }
