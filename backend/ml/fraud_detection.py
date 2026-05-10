"""
Fraud Detection Module
======================
Multi-signal fraud analysis for uploaded crop damage images:
  1. Duplicate image detection via perceptual hashing
  2. EXIF metadata validation (editing software, GPS mismatch)
  3. Timestamp consistency checks
  4. Image quality analysis
  5. Hash database for cross-claim duplicate detection
"""

import os
import random
from datetime import datetime

from .config import (
    HASH_DB_PATH,
    HASH_SIMILARITY_THRESHOLD,
    MIN_IMAGE_QUALITY_SCORE,
    SUSPICIOUS_FRAUD_THRESHOLD,
)
from .preprocess import extract_exif, image_quality_score
from .utils import (
    haversine_km,
    parse_gps_string,
    safe_json_load,
    safe_json_save,
    clamp,
)

# ---------------------------------------------------------------------------
# Lazy import for imagehash (optional dependency)
# ---------------------------------------------------------------------------
_imagehash = None
_PIL_Image = None


def _get_imagehash():
    global _imagehash, _PIL_Image
    if _imagehash is None:
        try:
            import imagehash
            from PIL import Image
            _imagehash = imagehash
            _PIL_Image = Image
        except ImportError:
            _imagehash = False  # sentinel: tried and failed
            _PIL_Image = False
    return _imagehash if _imagehash is not False else None


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def check_fraud(image_input=None,
                claim_gps: str = None,
                land_gps: str = None,
                user_id: str = None,
                claim_id: str = None) -> dict:
    """
    Run a comprehensive fraud analysis on a claim image.

    Parameters
    ----------
    image_input  : str | bytes | file-like | None
        The uploaded image (path, bytes, or file object).
    claim_gps    : str
        GPS coordinates from the claim submission (e.g. "17.38, 78.48").
    land_gps     : str
        GPS coordinates from the farmer's registered land record.
    user_id      : str
        Farmer user ID (used for cross-claim hash lookups).
    claim_id     : str
        Claim ID (stored alongside image hash for future lookups).

    Returns
    -------
    dict with keys:
        fraud_probability  (int 0–100)
        fraud_flags        (list of str)
        is_suspicious      (bool)
        details            (dict of per-check results)
    """
    flags = []
    scores = []  # list of (weight, score) — higher score = MORE fraud risk

    details = {}

    # --- 1. Duplicate image detection via perceptual hashing --------------
    dup_result = _check_duplicate(image_input, user_id, claim_id)
    details["duplicate_check"] = dup_result
    if dup_result["is_duplicate"]:
        flags.append("Possible duplicate image detected (matches a previous submission)")
        scores.append((0.35, 90))
    else:
        scores.append((0.35, 5))

    # --- 2. EXIF metadata validation --------------------------------------
    exif_result = _check_exif(image_input)
    details["exif_check"] = exif_result
    if exif_result["edited"]:
        flags.append(f"Image may have been edited with: {exif_result['software']}")
        scores.append((0.20, 70))
    else:
        scores.append((0.20, 5))

    # --- 3. Timestamp consistency -----------------------------------------
    ts_result = _check_timestamp(exif_result.get("datetime"))
    details["timestamp_check"] = ts_result
    if ts_result["suspicious"]:
        flags.append(ts_result["reason"])
        scores.append((0.10, 60))
    else:
        scores.append((0.10, 5))

    # --- 4. GPS mismatch between EXIF and claim/land ----------------------
    gps_result = _check_gps_mismatch(
        exif_gps=exif_result.get("gps"),
        claim_gps=claim_gps,
        land_gps=land_gps,
    )
    details["gps_check"] = gps_result
    if gps_result["mismatch"]:
        flags.append(gps_result["reason"])
        scores.append((0.20, 75))
    else:
        scores.append((0.20, 5))

    # --- 5. Image quality -------------------------------------------------
    quality = _check_quality(image_input)
    details["quality_check"] = quality
    if quality["low_quality"]:
        flags.append("Image quality is suspiciously low — possible screenshot or re-capture")
        scores.append((0.15, 55))
    else:
        scores.append((0.15, 5))

    # --- Aggregate --------------------------------------------------------
    fraud_probability = int(clamp(
        sum(w * s for w, s in scores) / sum(w for w, _ in scores)
        if scores else 10
    ))

    return {
        "fraud_probability": fraud_probability,
        "fraud_flags": flags,
        "is_suspicious": fraud_probability >= SUSPICIOUS_FRAUD_THRESHOLD,
        "details": details,
    }


def compute_image_hash(image_input) -> str | None:
    """Compute the perceptual hash (pHash) of an image.  Returns hex string."""
    ih = _get_imagehash()
    if ih is None or image_input is None:
        return None
    try:
        import io as _io
        if isinstance(image_input, str):
            img = _PIL_Image.open(image_input)
        elif isinstance(image_input, bytes):
            img = _PIL_Image.open(_io.BytesIO(image_input))
        else:
            raw = image_input.read()
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            img = _PIL_Image.open(_io.BytesIO(raw))
        return str(ih.phash(img))
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  INTERNAL CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def _check_duplicate(image_input, user_id: str = None,
                     claim_id: str = None) -> dict:
    """
    Compare the image's perceptual hash against previously stored hashes.
    """
    img_hash = compute_image_hash(image_input)
    if img_hash is None:
        return {"is_duplicate": False, "hash": None,
                "reason": "Hash computation skipped (imagehash not installed or no image)"}

    # Load existing hash database
    db = safe_json_load(HASH_DB_PATH, default={"hashes": []})
    hashes = db.get("hashes", [])

    # Check for near-duplicates
    ih = _get_imagehash()
    is_dup = False
    match_claim = None
    for entry in hashes:
        try:
            distance = ih.hex_to_hash(img_hash) - ih.hex_to_hash(entry["hash"])
            if distance <= HASH_SIMILARITY_THRESHOLD:
                # Ignore self-matches (same claim_id)
                if claim_id and entry.get("claim_id") == claim_id:
                    continue
                is_dup = True
                match_claim = entry.get("claim_id", "unknown")
                break
        except Exception:
            continue

    # Store the new hash
    hashes.append({
        "hash": img_hash,
        "user_id": user_id or "unknown",
        "claim_id": claim_id or "unknown",
        "timestamp": datetime.utcnow().isoformat(),
    })
    # Keep only the latest 5000 entries to bound storage
    db["hashes"] = hashes[-5000:]
    safe_json_save(HASH_DB_PATH, db)

    return {
        "is_duplicate": is_dup,
        "hash": img_hash,
        "matched_claim": match_claim,
        "reason": (f"Image matches previous claim {match_claim}" if is_dup
                   else "No duplicates found"),
    }


def _check_exif(image_input) -> dict:
    """Check EXIF metadata for signs of image editing."""
    if image_input is None:
        return {"edited": False, "software": None, "gps": None, "datetime": None}

    exif = extract_exif(image_input)

    # Known editing software signatures
    editing_software = [
        "photoshop", "gimp", "paint", "snapseed", "lightroom",
        "pixlr", "canva", "affinity", "corel",
    ]
    software = exif.get("software") or ""
    edited = any(s in software.lower() for s in editing_software)

    return {
        "edited": edited,
        "software": software if edited else None,
        "gps": exif.get("gps"),
        "datetime": exif.get("datetime"),
        "camera_make": exif.get("camera_make"),
        "camera_model": exif.get("camera_model"),
    }


def _check_timestamp(exif_datetime: str | None) -> dict:
    """Flag images with suspicious timestamps (too old or in the future)."""
    if not exif_datetime:
        return {"suspicious": False, "reason": "No EXIF timestamp available"}

    try:
        # EXIF datetime format: "2026:05:09 14:30:00"
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%Y:%m:%d", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(exif_datetime.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return {"suspicious": False, "reason": "Unparseable timestamp"}

        now = datetime.utcnow()
        diff_days = (now - dt).days

        if diff_days < -1:
            return {"suspicious": True,
                    "reason": f"Image timestamp is in the future ({exif_datetime})"}
        if diff_days > 90:
            return {"suspicious": True,
                    "reason": f"Image is {diff_days} days old — may not reflect current damage"}
        return {"suspicious": False, "reason": "Timestamp is recent and valid"}

    except Exception:
        return {"suspicious": False, "reason": "Timestamp parse error"}


def _check_gps_mismatch(exif_gps: dict | None,
                        claim_gps: str = None,
                        land_gps: str = None) -> dict:
    """
    Compare GPS coordinates from the image EXIF, the claim submission,
    and the registered land.
    """
    if exif_gps is None:
        return {"mismatch": False, "distance_km": None,
                "reason": "No GPS data in image EXIF"}

    exif_lat = exif_gps.get("latitude")
    exif_lon = exif_gps.get("longitude")
    if exif_lat is None or exif_lon is None:
        return {"mismatch": False, "distance_km": None,
                "reason": "Incomplete EXIF GPS data"}

    # Compare with land GPS first, then claim GPS
    ref_gps = parse_gps_string(land_gps) or parse_gps_string(claim_gps)
    if ref_gps is None:
        return {"mismatch": False, "distance_km": None,
                "reason": "No reference GPS to compare against"}

    dist = haversine_km(exif_lat, exif_lon, ref_gps[0], ref_gps[1])

    mismatch = dist > 50  # > 50 km is very suspicious
    return {
        "mismatch": mismatch,
        "distance_km": round(dist, 2),
        "reason": (f"Image was taken {dist:.1f} km from registered land"
                   if mismatch
                   else f"Image location is {dist:.1f} km from registered land (acceptable)"),
    }


def _check_quality(image_input) -> dict:
    """Check image quality score."""
    if image_input is None:
        return {"low_quality": False, "score": 50,
                "reason": "No image to assess"}

    score = image_quality_score(image_input)
    low = score < MIN_IMAGE_QUALITY_SCORE

    return {
        "low_quality": low,
        "score": score,
        "reason": (f"Image quality score {score}/100 is below threshold ({MIN_IMAGE_QUALITY_SCORE})"
                   if low
                   else f"Image quality score {score}/100 is acceptable"),
    }
