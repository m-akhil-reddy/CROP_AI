"""
Image Preprocessing Pipeline
=============================
Handles image loading, resizing, normalisation, noise reduction,
EXIF metadata extraction, and data-augmentation generators for training.
"""

import os
import io
import numpy as np

from .config import IMG_SIZE, IMG_CHANNELS

# ---------------------------------------------------------------------------
# Lazy imports — heavy libraries loaded only when needed
# ---------------------------------------------------------------------------
_cv2 = None
_PIL_Image = None


def _get_cv2():
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    return _cv2


def _get_pil():
    global _PIL_Image
    if _PIL_Image is None:
        from PIL import Image
        _PIL_Image = Image
    return _PIL_Image


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def load_and_preprocess(image_input, target_size=IMG_SIZE, denoise=True):
    """
    Load an image from *path* or *file-like object*, resize, denoise,
    and normalise to a float32 numpy array with shape (H, W, 3) in [0, 1].

    Parameters
    ----------
    image_input : str | bytes | file-like
        File path, raw bytes, or a file-like object (e.g. Flask request.files).
    target_size : tuple
        (height, width) to resize to.
    denoise : bool
        Apply light Gaussian blur for noise reduction.

    Returns
    -------
    np.ndarray  — shape (*target_size, 3), dtype float32, range [0, 1].
    """
    cv2 = _get_cv2()

    # --- Read image bytes -------------------------------------------------
    if isinstance(image_input, str):
        # File path
        img = cv2.imread(image_input, cv2.IMREAD_COLOR)
    elif isinstance(image_input, bytes):
        arr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        # File-like object (e.g. werkzeug FileStorage)
        raw = image_input.read()
        if hasattr(image_input, "seek"):
            image_input.seek(0)  # reset for later re-reads
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image from the provided input.")

    # --- Convert BGR → RGB ------------------------------------------------
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # --- Denoise (light Gaussian blur) ------------------------------------
    if denoise:
        img = cv2.GaussianBlur(img, (3, 3), 0)

    # --- Resize -----------------------------------------------------------
    img = cv2.resize(img, (target_size[1], target_size[0]),
                     interpolation=cv2.INTER_AREA)

    # --- Normalise to [0, 1] float32 -------------------------------------
    img = img.astype(np.float32) / 255.0

    return img


def preprocess_batch(image_paths, target_size=IMG_SIZE):
    """
    Preprocess a list of image paths into a batch tensor.

    Returns
    -------
    np.ndarray — shape (N, H, W, 3)
    """
    batch = []
    for p in image_paths:
        try:
            batch.append(load_and_preprocess(p, target_size))
        except Exception:
            continue
    if not batch:
        raise ValueError("No valid images in the batch.")
    return np.array(batch, dtype=np.float32)


# ═══════════════════════════════════════════════════════════════════════════
#  EXIF METADATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_exif(image_input) -> dict:
    """
    Extract useful EXIF metadata from an image.

    Returns a dict with keys like 'datetime', 'gps', 'software',
    'camera_make', 'camera_model'.  Missing fields are set to None.
    """
    Image = _get_pil()

    try:
        if isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            raw = image_input.read()
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            img = Image.open(io.BytesIO(raw))
    except Exception:
        return _empty_exif()

    exif_data = {}
    try:
        from PIL.ExifTags import TAGS, GPSTAGS
        raw_exif = img._getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
    except Exception:
        pass

    result = {
        "datetime": exif_data.get("DateTime") or exif_data.get("DateTimeOriginal"),
        "software": exif_data.get("Software"),
        "camera_make": exif_data.get("Make"),
        "camera_model": exif_data.get("Model"),
        "image_width": exif_data.get("ExifImageWidth") or (img.size[0] if img else None),
        "image_height": exif_data.get("ExifImageHeight") or (img.size[1] if img else None),
        "gps": _parse_gps_exif(exif_data.get("GPSInfo")),
        "orientation": exif_data.get("Orientation"),
    }
    return result


def _parse_gps_exif(gps_info) -> dict | None:
    """Parse EXIF GPSInfo dict into lat/lon floats."""
    if not gps_info or not isinstance(gps_info, dict):
        return None
    try:
        from PIL.ExifTags import GPSTAGS
        decoded = {}
        for k, v in gps_info.items():
            tag = GPSTAGS.get(k, k)
            decoded[tag] = v

        def _to_degrees(vals):
            d, m, s = [float(x) for x in vals]
            return d + m / 60.0 + s / 3600.0

        lat = _to_degrees(decoded["GPSLatitude"])
        if decoded.get("GPSLatitudeRef", "N") == "S":
            lat = -lat
        lon = _to_degrees(decoded["GPSLongitude"])
        if decoded.get("GPSLongitudeRef", "E") == "W":
            lon = -lon
        return {"latitude": round(lat, 6), "longitude": round(lon, 6)}
    except Exception:
        return None


def _empty_exif() -> dict:
    return {
        "datetime": None,
        "software": None,
        "camera_make": None,
        "camera_model": None,
        "image_width": None,
        "image_height": None,
        "gps": None,
        "orientation": None,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE QUALITY SCORE
# ═══════════════════════════════════════════════════════════════════════════

def image_quality_score(image_input) -> int:
    """
    Return a simple 0–100 quality score based on resolution and sharpness.
    Higher is better.
    """
    cv2 = _get_cv2()

    try:
        if isinstance(image_input, str):
            img = cv2.imread(image_input, cv2.IMREAD_GRAYSCALE)
        elif isinstance(image_input, bytes):
            arr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        else:
            raw = image_input.read()
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            arr = np.frombuffer(raw, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        return 50  # default mid-range on failure

    if img is None:
        return 50

    # Laplacian variance as sharpness proxy
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()

    # Resolution factor
    h, w = img.shape[:2]
    res_score = min(50, int((h * w) / (640 * 480) * 50))

    # Sharpness factor (laplacian variance; typical good image > 100)
    sharp_score = min(50, int(laplacian_var / 5))

    return min(100, res_score + sharp_score)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA AUGMENTATION (for training only)
# ═══════════════════════════════════════════════════════════════════════════

def get_training_augmentation():
    """
    Return a tf.keras ImageDataGenerator with augmentation for training.
    Only imported when explicitly needed (training script).
    """
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    return ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.25,
        horizontal_flip=True,
        vertical_flip=False,
        brightness_range=[0.7, 1.3],
        fill_mode="nearest",
    )


def get_validation_augmentation():
    """Return a tf.keras ImageDataGenerator with only rescaling (no augmentation)."""
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    return ImageDataGenerator(rescale=1.0 / 255)
