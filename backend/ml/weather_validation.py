"""
Weather Validation Module
=========================
Verifies that reported weather conditions are consistent with the
claimed damage type by checking recent weather data from the
OpenWeatherMap API.

Falls back to enhanced simulation when the API key is not configured.
"""

import os
import random
from datetime import datetime

from .config import OPENWEATHER_API_KEY, WEATHER_API_URL, DAMAGE_PROFILES
from .utils import parse_gps_string

# ---------------------------------------------------------------------------
# Lazy import for requests
# ---------------------------------------------------------------------------
_requests = None


def _get_requests():
    global _requests
    if _requests is None:
        import requests
        _requests = requests
    return _requests


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def verify_weather(gps_location: str = None,
                   damage_type: str = None,
                   district: str = None) -> dict:
    """
    Verify weather conditions at the claim location against the
    reported damage type.

    Parameters
    ----------
    gps_location : str   "lat, lon" from the claim.
    damage_type  : str   Damage class (e.g. "Flood", "Drought").
    district     : str   Fallback district name for the weather report.

    Returns
    -------
    dict with keys:
        weather_match   (bool)
        weather_score   (int 0–100)
        weather_data    (dict — temperature, humidity, description, etc.)
        report          (dict — event, description, severity, source)
    """
    coords = parse_gps_string(gps_location) if gps_location else None

    # Try real API first
    if OPENWEATHER_API_KEY and not OPENWEATHER_API_KEY.startswith("your_"):
        try:
            result = _real_weather_check(coords, damage_type, district)
            if result is not None:
                return result
        except Exception as e:
            print(f"[ML-Weather] API error: {e} — falling back to simulation")

    # Fallback to simulation
    return _simulated_weather_check(damage_type, district)


def generate_weather_report(district: str = None) -> dict:
    """
    Backward-compatible wrapper that returns a weather report dict
    matching the old ml_model.py interface.
    """
    result = verify_weather(district=district, damage_type=None)
    return result.get("report", {})


# ═══════════════════════════════════════════════════════════════════════════
#  REAL API IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════

def _real_weather_check(coords, damage_type: str, district: str) -> dict | None:
    """
    Query OpenWeatherMap Current Weather API and verify consistency
    with the claimed damage type.
    """
    requests = _get_requests()

    # Build query params
    params = {"appid": OPENWEATHER_API_KEY, "units": "metric"}
    if coords:
        params["lat"] = coords[0]
        params["lon"] = coords[1]
    elif district:
        params["q"] = f"{district},IN"
    else:
        return None  # no location available

    # --- Current weather ---
    resp = requests.get(f"{WEATHER_API_URL}/weather", params=params, timeout=8)
    if resp.status_code != 200:
        return None

    data = resp.json()

    weather_main = data.get("weather", [{}])[0].get("main", "").lower()
    weather_desc = data.get("weather", [{}])[0].get("description", "")
    temp = data.get("main", {}).get("temp", 0)
    humidity = data.get("main", {}).get("humidity", 0)
    wind_speed = data.get("wind", {}).get("speed", 0)
    rain_1h = data.get("rain", {}).get("1h", 0)
    rain_3h = data.get("rain", {}).get("3h", 0)
    city = data.get("name", district or "Unknown")

    weather_data = {
        "city": city,
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "description": weather_desc,
        "rain_1h_mm": rain_1h,
        "rain_3h_mm": rain_3h,
        "main": weather_main,
    }

    # --- Match scoring ---
    match_score, event, severity = _score_weather_match(
        damage_type, weather_main, weather_desc, temp, humidity, rain_3h
    )

    report = {
        "district": city,
        "event": event,
        "description": (f"Current: {weather_desc.capitalize()}, "
                        f"Temp: {temp}°C, Humidity: {humidity}%, "
                        f"Wind: {wind_speed} m/s, "
                        f"Rain (3h): {rain_3h}mm"),
        "severity": severity,
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "source": "OpenWeatherMap (Live Data)",
    }

    return {
        "weather_match": match_score >= 50,
        "weather_score": match_score,
        "weather_data": weather_data,
        "report": report,
    }


def _score_weather_match(damage_type: str, weather_main: str,
                         weather_desc: str, temp: float,
                         humidity: float, rain_3h: float) -> tuple:
    """
    Score how well current weather matches the damage type claim.
    Returns (score: int, event: str, severity: str).
    """
    score = 50  # neutral default
    event = weather_desc.capitalize() if weather_desc else "Normal Weather"
    severity = "Low"

    if damage_type is None:
        return score, event, severity

    damage_type_upper = damage_type.replace("_", " ").title()

    # Flood / Heavy Rain
    if damage_type in ("Flood", "Heavy_Rain"):
        if rain_3h > 50:
            score = 95
            severity = "Critical"
            event = f"Heavy Rainfall ({rain_3h}mm in 3h)"
        elif rain_3h > 20:
            score = 80
            severity = "High"
            event = f"Significant Rainfall ({rain_3h}mm in 3h)"
        elif "rain" in weather_main or "drizzle" in weather_main:
            score = 65
            severity = "Moderate"
            event = f"Rainfall detected ({weather_desc})"
        elif humidity > 80:
            score = 55
            severity = "Moderate"
            event = "High humidity conditions"
        else:
            score = 25
            severity = "Low"
            event = f"No rain detected — {weather_desc}"

    # Drought
    elif damage_type == "Drought":
        if temp > 40 and humidity < 30:
            score = 90
            severity = "Critical"
            event = f"Extreme heat ({temp}°C) and very low humidity ({humidity}%)"
        elif temp > 35 and humidity < 45:
            score = 75
            severity = "High"
            event = f"Hot and dry conditions ({temp}°C, {humidity}% humidity)"
        elif "clear" in weather_main or "sun" in weather_desc:
            score = 60
            severity = "Moderate"
            event = "Clear/dry weather"
        else:
            score = 30
            severity = "Low"
            event = f"Conditions not strongly drought-indicative — {weather_desc}"

    # Insect Attack
    elif damage_type == "Insect_Attack":
        if humidity > 70 and temp > 25:
            score = 75
            severity = "High"
            event = f"Warm and humid conditions favor pest activity ({temp}°C, {humidity}%)"
        elif humidity > 55:
            score = 60
            severity = "Moderate"
            event = "Moderate humidity — pest activity possible"
        else:
            score = 45
            severity = "Low"
            event = "Weather not strongly pest-favorable"

    # Disease
    elif damage_type == "Disease":
        if humidity > 75:
            score = 80
            severity = "High"
            event = f"High humidity ({humidity}%) — disease spread conditions"
        elif "rain" in weather_main or humidity > 60:
            score = 65
            severity = "Moderate"
            event = "Wet conditions support disease spread"
        else:
            score = 40
            severity = "Low"
            event = "Conditions not strongly disease-favorable"

    # Animal Damage / Nutrient Deficiency — weather neutral
    elif damage_type in ("Animal_Damage", "Nutrient_Deficiency"):
        score = 60
        severity = "Moderate"
        event = f"Weather neutral for {damage_type_upper}"

    # Healthy crop — no damage expected
    elif damage_type == "Healthy":
        score = 30
        severity = "Low"
        event = "Claim type is 'Healthy' — no damage expected"

    return int(score), event, severity


# ═══════════════════════════════════════════════════════════════════════════
#  SIMULATION FALLBACK
# ═══════════════════════════════════════════════════════════════════════════

_SIMULATED_EVENTS = [
    {"event": "Heavy Rainfall", "description": "Recent heavy rainfall detected. Cumulative: 245mm in last 72 hours.", "severity": "High"},
    {"event": "Flood Warning", "description": "Flood alert issued for nearby river basin. Water levels above danger mark.", "severity": "Critical"},
    {"event": "Cyclone Alert", "description": "Cyclonic circulation developing. Wind speeds up to 80 km/h expected.", "severity": "Critical"},
    {"event": "Drought Condition", "description": "Below-normal rainfall recorded for 3 consecutive months.", "severity": "High"},
    {"event": "Heatwave", "description": "Maximum temperature exceeded 44°C for 5 consecutive days.", "severity": "Moderate"},
    {"event": "Hailstorm", "description": "Hailstorm reported in adjacent mandal. Crop damage likely.", "severity": "High"},
    {"event": "Normal Weather", "description": "No significant weather anomalies detected.", "severity": "Low"},
]

_DISTRICTS = [
    "Hyderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam",
    "Nalgonda", "Adilabad", "Medak", "Rangareddy", "Mahbubnagar",
    "Guntur", "Krishna", "East Godavari", "West Godavari", "Prakasam",
]


def _simulated_weather_check(damage_type: str = None,
                             district: str = None) -> dict:
    """Generate a realistic simulated weather verification result."""
    if not district:
        district = random.choice(_DISTRICTS)

    # Pick an event that somewhat correlates with damage type
    if damage_type in ("Flood", "Heavy_Rain"):
        event = random.choice(_SIMULATED_EVENTS[:3])
        match_score = random.randint(65, 95)
    elif damage_type == "Drought":
        event = _SIMULATED_EVENTS[3]  # Drought Condition
        match_score = random.randint(60, 90)
    elif damage_type == "Healthy":
        event = _SIMULATED_EVENTS[-1]  # Normal Weather
        match_score = random.randint(30, 50)
    else:
        event = random.choice(_SIMULATED_EVENTS)
        match_score = random.randint(50, 85)

    weather_data = {
        "city": district,
        "temperature": round(random.uniform(22, 42), 1),
        "humidity": random.randint(30, 95),
        "wind_speed": round(random.uniform(1, 25), 1),
        "description": event["description"],
        "rain_1h_mm": round(random.uniform(0, 50), 1),
        "rain_3h_mm": round(random.uniform(0, 120), 1),
        "main": event["event"].lower().split()[0],
    }

    report = {
        "district": district,
        "event": event["event"],
        "description": event["description"],
        "severity": event["severity"],
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "source": "India Meteorological Department (Simulated)",
    }

    return {
        "weather_match": match_score >= 50,
        "weather_score": match_score,
        "weather_data": weather_data,
        "report": report,
    }
