"""
ML Configuration — Central settings for the AI pipeline.
=========================================================
All tuneable constants live here so nothing is hard-coded
across the codebase.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ML_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(_ML_DIR, "saved_models")
DATASET_DIR = os.path.join(_ML_DIR, "dataset")
TRAINING_RESULTS_DIR = os.path.join(_ML_DIR, "training_results")

MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "crop_damage_model.h5")
HASH_DB_PATH = os.path.join(SAVED_MODELS_DIR, "image_hash_db.json")

# ---------------------------------------------------------------------------
# Image settings
# ---------------------------------------------------------------------------
IMG_SIZE = (224, 224)          # EfficientNetB0 native resolution
IMG_CHANNELS = 3
BATCH_SIZE = 32

# ---------------------------------------------------------------------------
# Damage class labels (alphabetical order — must match training folder names)
# ---------------------------------------------------------------------------
DAMAGE_CLASSES = [
    "Animal_Damage",
    "Disease",
    "Drought",
    "Flood",
    "Healthy",
    "Heavy_Rain",
    "Insect_Attack",
    "Nutrient_Deficiency",
]

NUM_CLASSES = len(DAMAGE_CLASSES)

# Human-readable display names
DAMAGE_DISPLAY_NAMES = {
    "Animal_Damage":        "Animal Damage",
    "Disease":              "Disease Infection",
    "Drought":              "Drought Damage",
    "Flood":                "Flood Damage",
    "Healthy":              "Healthy Crop",
    "Heavy_Rain":           "Heavy Rain Damage",
    "Insect_Attack":        "Insect Attack",
    "Nutrient_Deficiency":  "Nutrient Deficiency",
}

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.40   # Minimum confidence to trust a prediction
HIGH_CONFIDENCE = 0.80

# ---------------------------------------------------------------------------
# Damage type profiles (recommendations, indicators, crop values)
# ---------------------------------------------------------------------------
DAMAGE_PROFILES = {
    "Flood": {
        "indicators": [
            "Water-logging detected in field area",
            "Crop submersion visible",
            "Soil erosion patterns identified",
            "Sediment deposits on crop surface",
        ],
        "severity_range": (40, 95),
        "recommendation": "Immediate drainage and replanting advisory issued.",
        "weather_keywords": ["rain", "flood", "storm", "cyclone"],
    },
    "Insect_Attack": {
        "indicators": [
            "Leaf damage patterns consistent with pest infestation",
            "Bore holes detected on stems",
            "Discoloration on crop canopy",
            "Chewed leaf edges observed",
        ],
        "severity_range": (20, 80),
        "recommendation": "Pesticide application recommended within 48 hours.",
        "weather_keywords": ["humid", "warm"],
    },
    "Drought": {
        "indicators": [
            "Soil moisture critically low",
            "Wilting observed across field",
            "Crop growth stunted significantly",
            "Leaf curling and browning detected",
        ],
        "severity_range": (30, 90),
        "recommendation": "Emergency irrigation support recommended.",
        "weather_keywords": ["dry", "heat", "hot", "clear"],
    },
    "Heavy_Rain": {
        "indicators": [
            "Crop lodging detected",
            "Excess water accumulation",
            "Physical damage to crop canopy",
            "Root exposure from soil washout",
        ],
        "severity_range": (25, 75),
        "recommendation": "Post-rain field assessment and drainage required.",
        "weather_keywords": ["rain", "storm", "drizzle"],
    },
    "Disease": {
        "indicators": [
            "Fungal spots detected on leaves",
            "Abnormal discoloration patterns",
            "Pathogen spread across crop rows",
            "Necrotic lesions on stems",
        ],
        "severity_range": (20, 85),
        "recommendation": "Fungicide treatment and quarantine of affected area.",
        "weather_keywords": ["humid", "rain", "mist"],
    },
    "Animal_Damage": {
        "indicators": [
            "Physical crop destruction patterns",
            "Trampling marks identified",
            "Irregular damage distribution",
            "Bite marks on crop stems",
        ],
        "severity_range": (15, 70),
        "recommendation": "Fencing and wildlife deterrent measures advised.",
        "weather_keywords": [],
    },
    "Healthy": {
        "indicators": [
            "Healthy green canopy detected",
            "Normal growth pattern observed",
            "No visible damage indicators",
        ],
        "severity_range": (0, 5),
        "recommendation": "No action required. Crop appears healthy.",
        "weather_keywords": [],
    },
    "Nutrient_Deficiency": {
        "indicators": [
            "Chlorosis (yellowing) of leaves detected",
            "Stunted growth pattern observed",
            "Interveinal discoloration present",
            "Purple tinting on leaf undersides",
        ],
        "severity_range": (15, 60),
        "recommendation": "Soil testing and targeted fertiliser application recommended.",
        "weather_keywords": [],
    },
}

# ---------------------------------------------------------------------------
# Crop economic values (₹ per acre per season)
# ---------------------------------------------------------------------------
CROP_VALUES = {
    "Rice":    45000,
    "Cotton":  55000,
    "Wheat":   40000,
    "Tomato":  60000,
    "Maize":   35000,
    "Sugarcane": 70000,
    "Groundnut": 50000,
    "Soybean": 42000,
}

COMPENSATION_RATIO = 0.75  # 75 % of estimated loss

# ---------------------------------------------------------------------------
# Scoring weights (must sum to 1.0)
# ---------------------------------------------------------------------------
SCORING_WEIGHTS = {
    "image_confidence": 0.40,
    "weather_match":    0.20,
    "gps_match":        0.15,
    "fraud_inverse":    0.15,
    "claim_history":    0.10,
}

# ---------------------------------------------------------------------------
# GPS validation
# ---------------------------------------------------------------------------
GPS_MATCH_THRESHOLD_KM = 10.0  # max acceptable distance in km

# ---------------------------------------------------------------------------
# Fraud detection
# ---------------------------------------------------------------------------
HASH_SIMILARITY_THRESHOLD = 5     # hamming distance for duplicate detection
MIN_IMAGE_QUALITY_SCORE = 20      # 0-100 quality scale
SUSPICIOUS_FRAUD_THRESHOLD = 50   # probability above which claim is flagged

# ---------------------------------------------------------------------------
# Weather API
# ---------------------------------------------------------------------------
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5"

# ---------------------------------------------------------------------------
# Training hyper-parameters
# ---------------------------------------------------------------------------
TRAIN_CONFIG = {
    "epochs": 30,
    "fine_tune_epochs": 15,
    "learning_rate": 1e-3,
    "fine_tune_lr": 1e-5,
    "train_split": 0.70,
    "val_split": 0.15,
    "test_split": 0.15,
    "dropout_rate": 0.3,
    "early_stop_patience": 5,
    "lr_reduce_patience": 3,
    "lr_reduce_factor": 0.5,
}

# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
ML_CONFIG = {
    "img_size": IMG_SIZE,
    "num_classes": NUM_CLASSES,
    "classes": DAMAGE_CLASSES,
    "model_path": MODEL_PATH,
    "confidence_threshold": CONFIDENCE_THRESHOLD,
}
