"""
AI-Based Crop Damage Assessment — Simulated ML Module
=====================================================
Provides simulated AI predictions for crop damage analysis.
Replace with real TensorFlow/OpenCV models for production use.
"""

import random


# ---------------------------------------------------------------------------
# Damage‑type descriptions used by the AI engine
# ---------------------------------------------------------------------------
DAMAGE_PROFILES = {
    "Flood": {
        "indicators": ["Water‑logging detected in field area", "Crop submersion visible", "Soil erosion patterns identified"],
        "severity_range": (40, 95),
        "recommendation": "Immediate drainage and replanting advisory issued.",
    },
    "Insect attack": {
        "indicators": ["Leaf damage patterns consistent with pest infestation", "Bore holes detected on stems", "Discoloration on crop canopy"],
        "severity_range": (20, 80),
        "recommendation": "Pesticide application recommended within 48 hours.",
    },
    "Drought": {
        "indicators": ["Soil moisture critically low", "Wilting observed across field", "Crop growth stunted significantly"],
        "severity_range": (30, 90),
        "recommendation": "Emergency irrigation support recommended.",
    },
    "Heavy rain": {
        "indicators": ["Crop lodging detected", "Excess water accumulation", "Physical damage to crop canopy"],
        "severity_range": (25, 75),
        "recommendation": "Post‑rain field assessment and drainage required.",
    },
    "Disease": {
        "indicators": ["Fungal spots detected on leaves", "Abnormal discoloration patterns", "Pathogen spread across crop rows"],
        "severity_range": (20, 85),
        "recommendation": "Fungicide treatment and quarantine of affected area.",
    },
    "Animal attack": {
        "indicators": ["Physical crop destruction patterns", "Trampling marks identified", "Irregular damage distribution"],
        "severity_range": (15, 70),
        "recommendation": "Fencing and wildlife deterrent measures advised.",
    },
}

CROP_VALUES = {
    "Rice": 45000,
    "Cotton": 55000,
    "Wheat": 40000,
    "Tomato": 60000,
    "Maize": 35000,
}

WEATHER_EVENTS = [
    {"event": "Heavy Rainfall", "description": "Recent heavy rainfall detected in this district. Cumulative: 245mm in last 72 hours.", "severity": "High"},
    {"event": "Flood Warning", "description": "Flood alert issued for nearby river basin. Water levels above danger mark.", "severity": "Critical"},
    {"event": "Cyclone Alert", "description": "Cyclonic circulation developing. Wind speeds up to 80 km/h expected.", "severity": "Critical"},
    {"event": "Drought Condition", "description": "Below‑normal rainfall recorded for 3 consecutive months in this region.", "severity": "High"},
    {"event": "Heatwave", "description": "Maximum temperature exceeded 44°C for 5 consecutive days.", "severity": "Moderate"},
    {"event": "Hailstorm", "description": "Hailstorm reported in adjacent mandal. Crop damage likely.", "severity": "High"},
    {"event": "Normal Weather", "description": "No significant weather anomalies detected in this district.", "severity": "Low"},
]

DISTRICTS = [
    "Hyderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam",
    "Nalgonda", "Adilabad", "Medak", "Rangareddy", "Mahbubnagar",
    "Guntur", "Krishna", "East Godavari", "West Godavari", "Prakasam",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_crop_damage(crop_type: str, damage_type: str, damage_percentage: int = None) -> dict:
    """
    Simulate AI analysis of crop damage.

    Returns a dict with:
      - ai_result   : human‑readable analysis string
      - ai_score    : confidence score 0‑100
      - indicators  : list of detected indicators
      - severity    : estimated severity label
      - recommendation : action recommendation
    """
    profile = DAMAGE_PROFILES.get(damage_type, DAMAGE_PROFILES["Flood"])

    # Confidence score
    base = random.randint(65, 96)
    ai_score = min(100, base + random.randint(-5, 10))

    # Pick 2‑3 indicators
    indicators = random.sample(profile["indicators"], k=min(len(profile["indicators"]), random.randint(2, 3)))

    # Severity
    if damage_percentage is None:
        damage_percentage = random.randint(*profile["severity_range"])

    if damage_percentage >= 70:
        severity = "Severe"
    elif damage_percentage >= 40:
        severity = "Moderate"
    else:
        severity = "Mild"

    ai_result = (
        f"AI Analysis Complete — {damage_type} damage detected on {crop_type} crop. "
        f"Severity: {severity} ({damage_percentage}% affected). "
        f"Confidence: {ai_score}%. "
        f"Indicators: {'; '.join(indicators)}. "
        f"Recommendation: {profile['recommendation']}"
    )

    return {
        "ai_result": ai_result,
        "ai_score": ai_score,
        "damage_percentage": damage_percentage,
        "severity": severity,
        "indicators": indicators,
        "recommendation": profile["recommendation"],
        "crop_type": crop_type,
        "damage_type": damage_type,
    }


def calculate_eligibility_score(damage_percentage: int, crop_stage: str, has_weather_event: bool = True) -> dict:
    """
    Calculate a claim eligibility score (0–100).

    Scoring factors:
      - damage_percentage contributes up to 50 pts
      - crop_stage contributes up to 25 pts
      - weather event adds up to 25 pts
    """
    # Damage component (0‑50)
    damage_score = min(50, int(damage_percentage * 0.55))

    # Crop stage component (0‑25)
    stage_scores = {
        "Seed stage": 15,
        "Growing stage": 20,
        "Harvest stage": 25,
    }
    stage_score = stage_scores.get(crop_stage, 15)

    # Weather component (0‑25)
    weather_score = random.randint(15, 25) if has_weather_event else random.randint(5, 12)

    total = min(100, damage_score + stage_score + weather_score)

    if total >= 80:
        status = "Highly Eligible"
        color = "green"
    elif total >= 50:
        status = "Moderately Eligible"
        color = "yellow"
    else:
        status = "Low Eligibility"
        color = "red"

    return {
        "eligibility_score": total,
        "status": status,
        "color": color,
        "breakdown": {
            "damage_component": damage_score,
            "crop_stage_component": stage_score,
            "weather_component": weather_score,
        },
    }


def generate_weather_report(district: str = None) -> dict:
    """Return a simulated weather/calamity report for a district."""
    if district is None:
        district = random.choice(DISTRICTS)

    event = random.choice(WEATHER_EVENTS)

    return {
        "district": district,
        "event": event["event"],
        "description": event["description"],
        "severity": event["severity"],
        "report_date": "2026‑05‑09",
        "source": "India Meteorological Department (Simulated)",
    }


def estimate_loss(crop_type: str, damage_percentage: int, land_area_acres: float = 1.0) -> dict:
    """Estimate financial loss based on crop type, damage, and area."""
    base_value = CROP_VALUES.get(crop_type, 40000)
    total_value = base_value * land_area_acres
    loss = total_value * (damage_percentage / 100)
    compensation = loss * 0.75  # 75 % compensation ratio

    return {
        "crop_value_per_acre": base_value,
        "total_crop_value": round(total_value, 2),
        "estimated_loss": round(loss, 2),
        "compensation_amount": round(compensation, 2),
        "compensation_ratio": "75%",
    }
