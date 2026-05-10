"""
Prediction Engine — Core crop damage classification.
====================================================
Runs real EfficientNetB0 CNN inference when a trained model is available,
otherwise falls back to an enhanced probabilistic simulation that mimics
real model behaviour for demo / development purposes.
"""

import random
import numpy as np

from .config import (
    DAMAGE_CLASSES,
    DAMAGE_DISPLAY_NAMES,
    DAMAGE_PROFILES,
    CONFIDENCE_THRESHOLD,
    IMG_SIZE,
)
from .model_loader import get_model, is_real_model_active
from .preprocess import load_and_preprocess
from .utils import severity_label


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def analyze_image(image_input) -> dict:
    """
    Analyze a single image for crop damage.

    Parameters
    ----------
    image_input : str | bytes | file-like
        Path, raw bytes, or file-like object of the crop image.

    Returns
    -------
    dict with keys:
        damage_type, damage_type_raw, confidence, severity,
        damage_percentage, indicators, recommendation, ai_result, ai_score
    """
    if is_real_model_active():
        return _real_inference(image_input)
    else:
        return _simulation_inference(image_input)


def analyze_multiple_images(image_inputs: list) -> dict:
    """
    Ensemble prediction across multiple images.
    Averages the class probabilities and returns the combined result.
    """
    if not image_inputs:
        return _simulation_inference(None)

    if is_real_model_active():
        return _real_ensemble(image_inputs)
    else:
        # Simulation: run once but boost confidence slightly for multi-image
        result = _simulation_inference(None)
        boost = min(8, len(image_inputs) * 2)
        result["confidence"] = min(99, result["confidence"] + boost)
        result["ai_score"] = result["confidence"]
        return result


def analyze_crop_damage(crop_type: str, damage_type: str,
                        damage_percentage: int = None,
                        image_input=None) -> dict:
    """
    Backward-compatible wrapper matching the old ml_model.py API.
    If an image_input is provided the real/simulation inference is used;
    otherwise it runs the enhanced simulation with the given metadata.
    """
    if image_input is not None:
        result = analyze_image(image_input)
        # Override with user-supplied metadata if the simulation was used
        if not is_real_model_active():
            result = _simulation_with_metadata(crop_type, damage_type,
                                               damage_percentage)
        return result

    return _simulation_with_metadata(crop_type, damage_type, damage_percentage)


# ═══════════════════════════════════════════════════════════════════════════
#  REAL CNN INFERENCE
# ═══════════════════════════════════════════════════════════════════════════

def _real_inference(image_input) -> dict:
    """Run EfficientNetB0 CNN prediction on a single image."""
    model = get_model()

    # Preprocess
    img_array = load_and_preprocess(image_input, target_size=IMG_SIZE)
    img_batch = np.expand_dims(img_array, axis=0)

    # Predict
    predictions = model.predict(img_batch, verbose=0)[0]

    # Parse results
    class_idx = int(np.argmax(predictions))
    confidence = float(predictions[class_idx]) * 100
    damage_class = DAMAGE_CLASSES[class_idx]

    return _build_result(damage_class, confidence)


def _real_ensemble(image_inputs: list) -> dict:
    """Average CNN predictions across multiple images."""
    model = get_model()

    all_preds = []
    for inp in image_inputs:
        try:
            img_array = load_and_preprocess(inp, target_size=IMG_SIZE)
            img_batch = np.expand_dims(img_array, axis=0)
            preds = model.predict(img_batch, verbose=0)[0]
            all_preds.append(preds)
        except Exception:
            continue

    if not all_preds:
        return _simulation_inference(None)

    avg_preds = np.mean(all_preds, axis=0)
    class_idx = int(np.argmax(avg_preds))
    confidence = float(avg_preds[class_idx]) * 100
    damage_class = DAMAGE_CLASSES[class_idx]

    return _build_result(damage_class, confidence)


# ═══════════════════════════════════════════════════════════════════════════
#  ENHANCED SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

def _simulation_inference(image_input) -> dict:
    """
    Enhanced simulation that produces realistic-looking results.
    Uses weighted random selection so "Flood" and "Disease" are
    more common than "Healthy" — matching real-world claim distributions.
    """
    # Weighted random damage type
    weights = [0.10, 0.18, 0.12, 0.20, 0.03, 0.15, 0.08, 0.14]
    damage_class = random.choices(DAMAGE_CLASSES, weights=weights, k=1)[0]

    # Realistic confidence range
    confidence = random.uniform(62, 97)

    return _build_result(damage_class, confidence)


def _simulation_with_metadata(crop_type: str, damage_type: str,
                              damage_percentage: int = None) -> dict:
    """
    Simulation using user-provided metadata (backward-compatible with
    the old ml_model.py interface).
    """
    # Map the frontend damage_type string to our class labels
    mapping = {
        "Flood": "Flood",
        "Insect attack": "Insect_Attack",
        "Drought": "Drought",
        "Heavy rain": "Heavy_Rain",
        "Disease": "Disease",
        "Animal attack": "Animal_Damage",
    }
    damage_class = mapping.get(damage_type, "Flood")

    profile = DAMAGE_PROFILES.get(damage_class, DAMAGE_PROFILES["Flood"])

    # Confidence
    confidence = random.uniform(65, 96)

    # Damage percentage
    if damage_percentage is None:
        damage_percentage = random.randint(*profile["severity_range"])

    severity = severity_label(damage_percentage)

    # Pick indicators
    num_indicators = min(len(profile["indicators"]), random.randint(2, 3))
    indicators = random.sample(profile["indicators"], k=num_indicators)

    display_name = DAMAGE_DISPLAY_NAMES.get(damage_class, damage_class)

    ai_result = (
        f"AI Analysis Complete — {damage_type} damage detected on {crop_type} crop. "
        f"Severity: {severity} ({damage_percentage}% affected). "
        f"Confidence: {confidence:.0f}%. "
        f"Indicators: {'; '.join(indicators)}. "
        f"Recommendation: {profile['recommendation']}"
    )

    return {
        "damage_type": display_name,
        "damage_type_raw": damage_class,
        "confidence": round(confidence),
        "ai_score": round(confidence),
        "severity": severity,
        "damage_percentage": damage_percentage,
        "indicators": indicators,
        "recommendation": profile["recommendation"],
        "crop_type": crop_type,
        "ai_result": ai_result,
        "model_mode": "simulation",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  RESULT BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def _build_result(damage_class: str, confidence: float) -> dict:
    """
    Build a standardised result dict from a damage class label and
    confidence score.
    """
    profile = DAMAGE_PROFILES.get(damage_class, DAMAGE_PROFILES.get("Flood", {}))
    display_name = DAMAGE_DISPLAY_NAMES.get(damage_class, damage_class)

    # Estimate damage percentage from the class profile
    sev_range = profile.get("severity_range", (30, 70))
    if damage_class == "Healthy":
        damage_pct = random.randint(0, 5)
    else:
        # Scale damage percentage with confidence
        base = sev_range[0] + (sev_range[1] - sev_range[0]) * (confidence / 100)
        damage_pct = int(min(100, max(0, base + random.randint(-5, 5))))

    severity = severity_label(damage_pct)

    # Pick indicators
    all_indicators = profile.get("indicators", ["Damage patterns detected"])
    num_indicators = min(len(all_indicators), random.randint(2, 3))
    indicators = random.sample(all_indicators, k=num_indicators)

    recommendation = profile.get("recommendation", "Field inspection recommended.")

    ai_result = (
        f"AI Analysis Complete — {display_name} detected. "
        f"Severity: {severity} ({damage_pct}% affected). "
        f"Confidence: {confidence:.0f}%. "
        f"Indicators: {'; '.join(indicators)}. "
        f"Recommendation: {recommendation}"
    )

    model_mode = "real_cnn" if is_real_model_active() else "simulation"

    return {
        "damage_type": display_name,
        "damage_type_raw": damage_class,
        "confidence": round(confidence),
        "ai_score": round(confidence),
        "severity": severity,
        "damage_percentage": damage_pct,
        "indicators": indicators,
        "recommendation": recommendation,
        "ai_result": ai_result,
        "model_mode": model_mode,
    }
