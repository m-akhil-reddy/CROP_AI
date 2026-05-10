"""
Scoring Engine — Weighted eligibility score calculation.
========================================================
Combines signals from:
  • Image AI confidence  (40 %)
  • Weather match        (20 %)
  • GPS match            (15 %)
  • Fraud inverse        (15 %)
  • Claim history        (10 %)

Also provides loss estimation and backward-compatible helpers.
"""

import random

from .config import (
    SCORING_WEIGHTS,
    CROP_VALUES,
    COMPENSATION_RATIO,
    GPS_MATCH_THRESHOLD_KM,
)
from .utils import haversine_km, parse_gps_string, clamp, severity_label


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def calculate_final_score(
    ai_confidence: int = 70,
    weather_score: int = 60,
    gps_match_score: int = 80,
    fraud_probability: int = 10,
    claim_history_score: int = 70,
) -> dict:
    """
    Calculate the final weighted eligibility score.

    Parameters
    ----------
    ai_confidence      : 0–100 from the image prediction
    weather_score      : 0–100 from weather verification
    gps_match_score    : 0–100 from GPS distance validation
    fraud_probability  : 0–100 (higher = more fraud risk)
    claim_history_score: 0–100 (higher = better history)

    Returns
    -------
    dict with eligibility_score, status, color, risk_level, breakdown
    """
    w = SCORING_WEIGHTS

    fraud_inverse = max(0, 100 - fraud_probability)

    raw = (
        w["image_confidence"] * ai_confidence +
        w["weather_match"]    * weather_score +
        w["gps_match"]        * gps_match_score +
        w["fraud_inverse"]    * fraud_inverse +
        w["claim_history"]    * claim_history_score
    )

    total = int(clamp(raw, 0, 100))

    if total >= 80:
        status = "Highly Eligible"
        color = "green"
        risk_level = "Low Risk"
    elif total >= 50:
        status = "Moderately Eligible"
        color = "yellow"
        risk_level = "Medium Risk"
    else:
        status = "Low Eligibility"
        color = "red"
        risk_level = "High Risk"

    return {
        "eligibility_score": total,
        "status": status,
        "color": color,
        "risk_level": risk_level,
        "breakdown": {
            "image_confidence_component": round(w["image_confidence"] * ai_confidence, 1),
            "weather_match_component": round(w["weather_match"] * weather_score, 1),
            "gps_match_component": round(w["gps_match"] * gps_match_score, 1),
            "fraud_inverse_component": round(w["fraud_inverse"] * fraud_inverse, 1),
            "claim_history_component": round(w["claim_history"] * claim_history_score, 1),
        },
    }


def calculate_eligibility_score(damage_percentage: int,
                                crop_stage: str,
                                has_weather_event: bool = True) -> dict:
    """
    Backward-compatible eligibility scorer matching the old ml_model.py API.
    Uses the new weighted system internally but presents the same output shape.
    """
    # Damage → image confidence proxy
    ai_confidence = min(100, int(damage_percentage * 1.1) + random.randint(5, 15))

    # Crop stage component
    stage_boost = {"Seed stage": 65, "Growing stage": 75, "Harvest stage": 90}
    stage_score = stage_boost.get(crop_stage, 70)

    # Weather component
    weather_score = random.randint(60, 95) if has_weather_event else random.randint(30, 55)

    # Assume no fraud and decent history for backward compat
    fraud_prob = random.randint(5, 20)
    history_score = random.randint(60, 85)

    result = calculate_final_score(
        ai_confidence=ai_confidence,
        weather_score=weather_score,
        gps_match_score=random.randint(70, 95),
        fraud_probability=fraud_prob,
        claim_history_score=history_score,
    )

    return result


def calculate_gps_match_score(claim_gps: str = None,
                              land_gps: str = None) -> dict:
    """
    Calculate a GPS match score based on distance between claim
    location and registered land.

    Returns
    -------
    dict with gps_match (bool), gps_score (int 0–100), distance_km (float)
    """
    c = parse_gps_string(claim_gps)
    l = parse_gps_string(land_gps)

    if c is None or l is None:
        # Can't verify — give neutral score
        return {
            "gps_match": True,
            "gps_score": 70,
            "distance_km": None,
            "reason": "GPS comparison not possible (missing coordinates)",
        }

    dist = haversine_km(c[0], c[1], l[0], l[1])

    if dist <= 1.0:
        score = 100
    elif dist <= GPS_MATCH_THRESHOLD_KM:
        # Linear decay from 100 to 50 over the threshold
        score = int(100 - (dist / GPS_MATCH_THRESHOLD_KM) * 50)
    elif dist <= 50:
        score = int(50 - ((dist - GPS_MATCH_THRESHOLD_KM) / 40) * 30)
    else:
        score = max(5, int(20 - dist / 100))

    score = int(clamp(score, 0, 100))

    return {
        "gps_match": dist <= GPS_MATCH_THRESHOLD_KM,
        "gps_score": score,
        "distance_km": round(dist, 2),
        "reason": (f"Claim location is {dist:.1f} km from registered land"
                   + (" (within threshold)" if dist <= GPS_MATCH_THRESHOLD_KM
                      else " (EXCEEDS threshold)")),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  LOSS ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════

def estimate_loss(crop_type: str, damage_percentage: int,
                  land_area_acres: float = 1.0) -> dict:
    """
    Estimate financial loss based on crop type, damage percentage,
    and land area.  Backward-compatible with old ml_model.py.
    """
    base_value = CROP_VALUES.get(crop_type, 40000)
    total_value = base_value * land_area_acres
    loss = total_value * (damage_percentage / 100)
    compensation = loss * COMPENSATION_RATIO

    return {
        "crop_value_per_acre": base_value,
        "total_crop_value": round(total_value, 2),
        "estimated_loss": round(loss, 2),
        "compensation_amount": round(compensation, 2),
        "compensation_ratio": f"{int(COMPENSATION_RATIO * 100)}%",
    }
