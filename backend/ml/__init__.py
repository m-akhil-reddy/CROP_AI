"""
AI-Based Crop Damage Assessment — Real ML Module
=================================================
Production-grade ML pipeline for crop damage classification,
fraud detection, weather validation, and eligibility scoring.

When a trained model exists at saved_models/crop_damage_model.h5,
the system uses real EfficientNetB0 CNN inference.
Otherwise it falls back to an enhanced simulation engine so
the application always works out of the box.
"""

from .predict import analyze_crop_damage, analyze_image, analyze_multiple_images
from .scoring import calculate_eligibility_score, estimate_loss, calculate_final_score
from .fraud_detection import check_fraud, compute_image_hash
from .weather_validation import verify_weather, generate_weather_report
from .model_loader import get_model, is_real_model_active
from .config import ML_CONFIG, DAMAGE_CLASSES

__all__ = [
    "analyze_crop_damage",
    "analyze_image",
    "analyze_multiple_images",
    "calculate_eligibility_score",
    "estimate_loss",
    "calculate_final_score",
    "check_fraud",
    "compute_image_hash",
    "verify_weather",
    "generate_weather_report",
    "get_model",
    "is_real_model_active",
    "ML_CONFIG",
    "DAMAGE_CLASSES",
]
