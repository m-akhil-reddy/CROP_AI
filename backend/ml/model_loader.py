"""
Model Loader — Smart loading with automatic fallback.
=====================================================
* If a trained .h5 model exists → load real EfficientNetB0 CNN
* If not → set a flag so the predict module uses enhanced simulation
* Thread-safe singleton pattern for the model instance
"""

import os
import threading

from .config import MODEL_PATH, IMG_SIZE, NUM_CLASSES, DAMAGE_CLASSES

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_model = None
_model_lock = threading.Lock()
_real_model_active = False
_model_loaded = False


def is_real_model_active() -> bool:
    """Return True if a real trained CNN model is loaded."""
    _ensure_loaded()
    return _real_model_active


def get_model():
    """
    Return the loaded Keras model instance, or None if running in
    simulation mode.  The first call triggers loading; subsequent calls
    return the cached instance.
    """
    _ensure_loaded()
    return _model


# ---------------------------------------------------------------------------
# Internal loader (runs once)
# ---------------------------------------------------------------------------

def _ensure_loaded():
    global _model, _real_model_active, _model_loaded

    if _model_loaded:
        return

    with _model_lock:
        if _model_loaded:
            return  # double-check after acquiring lock

        if os.path.isfile(MODEL_PATH):
            try:
                _model = _load_real_model(MODEL_PATH)
                _real_model_active = True
                print(f"[ML] [OK] Real CNN model loaded from {MODEL_PATH}")
                print(f"[ML]    Input shape : {_model.input_shape}")
                print(f"[ML]    Classes     : {NUM_CLASSES}")

                # Warm-up inference to pre-compile XLA / graph
                _warmup(_model)

            except Exception as e:
                print(f"[ML] [WARN] Failed to load model: {e}")
                print("[ML]    Falling back to enhanced simulation mode.")
                _model = None
                _real_model_active = False
        else:
            print(f"[ML] [INFO] No trained model found at {MODEL_PATH}")
            print("[ML]    Running in enhanced simulation mode.")
            print("[ML]    To enable real inference, train a model with:")
            print("[ML]       python -m ml.train")
            _model = None
            _real_model_active = False

        _model_loaded = True


def _load_real_model(path: str):
    """Load a Keras .h5 or SavedModel from disk."""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # suppress TF info noise

    import tensorflow as tf
    model = tf.keras.models.load_model(path, compile=False)

    # Re-compile with standard metrics
    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def _warmup(model):
    """Run a single dummy inference to pre-compile the graph."""
    import numpy as np
    dummy = np.zeros((1, *IMG_SIZE, 3), dtype=np.float32)
    try:
        model.predict(dummy, verbose=0)
        print("[ML]    Model warm-up complete.")
    except Exception:
        pass  # non-critical


# ═══════════════════════════════════════════════════════════════════════════
#  MODEL BUILDER (used by train.py)
# ═══════════════════════════════════════════════════════════════════════════

def build_efficientnet_model(num_classes: int = NUM_CLASSES,
                             input_shape=(224, 224, 3),
                             dropout_rate: float = 0.3,
                             freeze_base: bool = True):
    """
    Build an EfficientNetB0-based classification model with transfer learning.

    Architecture
    ------------
    EfficientNetB0 (ImageNet weights, frozen)
       → GlobalAveragePooling2D
       → BatchNormalization
       → Dense(256, relu)
       → Dropout
       → BatchNormalization
       → Dense(num_classes, softmax)

    Parameters
    ----------
    num_classes  : number of output categories
    input_shape  : (H, W, C)
    dropout_rate : dropout probability
    freeze_base  : if True, freeze all EfficientNetB0 layers initially

    Returns
    -------
    tf.keras.Model  (un-compiled)
    """
    import tensorflow as tf
    from tensorflow.keras import layers, Model

    base = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=input_shape,
    )

    if freeze_base:
        base.trainable = False

    x = base.output
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.BatchNormalization(name="bn1")(x)
    x = layers.Dense(256, activation="relu", name="fc1")(x)
    x = layers.Dropout(dropout_rate, name="drop1")(x)
    x = layers.BatchNormalization(name="bn2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = Model(inputs=base.input, outputs=outputs, name="CropDamageNet")
    return model


def unfreeze_top_layers(model, num_layers: int = 20):
    """
    Unfreeze the top *num_layers* of the base model for fine-tuning.
    Call this after the initial training phase.
    """
    # The base model is the first layer (Functional model)
    base = model.layers[0] if hasattr(model.layers[0], "layers") else None
    if base is None:
        # Flat model — unfreeze from the end
        for layer in model.layers[-num_layers:]:
            layer.trainable = True
    else:
        base.trainable = True
        for layer in base.layers[:-num_layers]:
            layer.trainable = False

    return model
