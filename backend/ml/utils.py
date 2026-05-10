"""
ML Utilities — Shared helpers used across the ML package.
=========================================================
"""

import os
import math
import json
from datetime import datetime


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in km between two GPS points
    using the Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_gps_string(gps_str: str):
    """
    Parse a GPS string like "17.385044, 78.486671" into (lat, lon) floats.
    Returns None if the string cannot be parsed.
    """
    if not gps_str or not isinstance(gps_str, str):
        return None
    try:
        parts = [p.strip() for p in gps_str.split(",")]
        if len(parts) != 2:
            return None
        return float(parts[0]), float(parts[1])
    except (ValueError, IndexError):
        return None


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def safe_json_load(path: str, default=None):
    """Load a JSON file, returning *default* if it doesn't exist or is corrupt."""
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def safe_json_save(path: str, data):
    """Atomically save data to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)


def severity_label(damage_pct: float) -> str:
    """Convert a 0–100 damage percentage to a human-readable severity label."""
    if damage_pct >= 70:
        return "Severe"
    elif damage_pct >= 40:
        return "Moderate"
    elif damage_pct >= 15:
        return "Mild"
    else:
        return "Minimal"


def timestamp_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.utcnow().isoformat()


def format_currency_inr(amount: float) -> str:
    """Format a number as Indian Rupees (₹)."""
    return f"₹{amount:,.2f}"
