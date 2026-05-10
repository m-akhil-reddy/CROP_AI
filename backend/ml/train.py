"""
Training Pipeline — EfficientNetB0 Transfer Learning
====================================================
Standalone script for training the crop damage classification model.

Usage
-----
    cd backend
    python -m ml.train

Dataset layout
--------------
    backend/ml/dataset/
    ├── Animal_Damage/
    │   ├── img001.jpg
    │   └── ...
    ├── Disease/
    ├── Drought/
    ├── Flood/
    ├── Healthy/
    ├── Heavy_Rain/
    ├── Insect_Attack/
    └── Nutrient_Deficiency/

Each subfolder name must exactly match the labels in config.DAMAGE_CLASSES.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

# Ensure the backend directory is on sys.path so relative imports work
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from ml.config import (
    DATASET_DIR, SAVED_MODELS_DIR, TRAINING_RESULTS_DIR,
    IMG_SIZE, NUM_CLASSES, DAMAGE_CLASSES, BATCH_SIZE,
    TRAIN_CONFIG, MODEL_PATH,
)


def main():
    """Full training pipeline."""
    print("=" * 60)
    print("  Crop Damage Classification — Model Training")
    print("=" * 60)

    # ── Validate dataset ──────────────────────────────────────────────
    if not os.path.isdir(DATASET_DIR):
        print(f"\n[ERROR] Dataset directory not found: {DATASET_DIR}")
        print("        Please create it and add class sub-folders.")
        print("        See: backend/ml/dataset/README.md")
        sys.exit(1)

    class_dirs = [d for d in os.listdir(DATASET_DIR)
                  if os.path.isdir(os.path.join(DATASET_DIR, d))]
    if len(class_dirs) < 2:
        print(f"\n[ERROR] Need at least 2 class folders, found: {class_dirs}")
        sys.exit(1)

    total_images = sum(
        len([f for f in os.listdir(os.path.join(DATASET_DIR, d))
             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))])
        for d in class_dirs
    )
    print(f"\n[INFO] Dataset: {DATASET_DIR}")
    print(f"[INFO] Classes: {class_dirs}")
    print(f"[INFO] Total images: {total_images}")

    if total_images < 50:
        print("[WARN] Very small dataset — results will be unreliable.")

    # ── Imports (heavy — only when actually training) ─────────────────
    print("\n[1/7] Loading TensorFlow...")
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import (
        EarlyStopping, ReduceLROnPlateau, ModelCheckpoint,
    )
    print(f"       TensorFlow {tf.__version__}")
    print(f"       GPU: {tf.config.list_physical_devices('GPU') or 'None (CPU mode)'}")

    # ── Data generators ───────────────────────────────────────────────
    print("\n[2/7] Preparing data generators...")

    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.25,
        horizontal_flip=True,
        brightness_range=[0.7, 1.3],
        fill_mode="nearest",
        validation_split=1 - TRAIN_CONFIG["train_split"],
    )

    val_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=1 - TRAIN_CONFIG["train_split"],
    )

    common_params = dict(
        directory=DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
        seed=42,
    )

    train_data = train_gen.flow_from_directory(
        **common_params, subset="training",
    )
    val_data = val_gen.flow_from_directory(
        **common_params, subset="validation",
    )

    # Store class mapping
    class_indices = train_data.class_indices
    print(f"       Classes found: {class_indices}")
    print(f"       Training samples: {train_data.samples}")
    print(f"       Validation samples: {val_data.samples}")

    # ── Build model ───────────────────────────────────────────────────
    print("\n[3/7] Building EfficientNetB0 model...")
    from ml.model_loader import build_efficientnet_model

    num_detected_classes = len(class_indices)
    model = build_efficientnet_model(
        num_classes=num_detected_classes,
        input_shape=(*IMG_SIZE, 3),
        dropout_rate=TRAIN_CONFIG["dropout_rate"],
        freeze_base=True,
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=TRAIN_CONFIG["learning_rate"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.summary()

    # ── Callbacks ─────────────────────────────────────────────────────
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
    os.makedirs(TRAINING_RESULTS_DIR, exist_ok=True)

    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=TRAIN_CONFIG["early_stop_patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=TRAIN_CONFIG["lr_reduce_factor"],
            patience=TRAIN_CONFIG["lr_reduce_patience"],
            min_lr=1e-7,
            verbose=1,
        ),
        ModelCheckpoint(
            MODEL_PATH,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
    ]

    # ── Phase 1: Transfer learning (base frozen) ─────────────────────
    print("\n[4/7] Phase 1 — Transfer Learning (base frozen)...")
    history1 = model.fit(
        train_data,
        validation_data=val_data,
        epochs=TRAIN_CONFIG["epochs"],
        callbacks=callbacks,
        verbose=1,
    )

    # ── Phase 2: Fine-tuning (top layers unfrozen) ───────────────────
    print("\n[5/7] Phase 2 — Fine-Tuning (unfreezing top 20 layers)...")
    from ml.model_loader import unfreeze_top_layers

    model = unfreeze_top_layers(model, num_layers=20)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=TRAIN_CONFIG["fine_tune_lr"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        train_data,
        validation_data=val_data,
        epochs=TRAIN_CONFIG["fine_tune_epochs"],
        callbacks=callbacks,
        verbose=1,
    )

    # ── Save final model ─────────────────────────────────────────────
    print(f"\n[6/7] Saving model to {MODEL_PATH}...")
    model.save(MODEL_PATH)
    print("       Model saved successfully!")

    # Save class mapping
    mapping_path = os.path.join(SAVED_MODELS_DIR, "class_mapping.json")
    with open(mapping_path, "w") as f:
        json.dump(class_indices, f, indent=2)
    print(f"       Class mapping saved to {mapping_path}")

    # ── Generate visualisations ──────────────────────────────────────
    print("\n[7/7] Generating training visualisations...")
    _generate_plots(history1, history2, TRAINING_RESULTS_DIR)
    _generate_confusion_matrix(model, val_data, class_indices, TRAINING_RESULTS_DIR)

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE!")
    print(f"  Model:  {MODEL_PATH}")
    print(f"  Graphs: {TRAINING_RESULTS_DIR}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
#  VISUALISATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _generate_plots(history1, history2, output_dir):
    """Generate accuracy and loss plots."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Merge histories
        acc = history1.history.get("accuracy", []) + history2.history.get("accuracy", [])
        val_acc = history1.history.get("val_accuracy", []) + history2.history.get("val_accuracy", [])
        loss = history1.history.get("loss", []) + history2.history.get("loss", [])
        val_loss = history1.history.get("val_loss", []) + history2.history.get("val_loss", [])

        epochs_range = range(1, len(acc) + 1)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Accuracy
        ax1.plot(epochs_range, acc, label="Train Accuracy", linewidth=2)
        ax1.plot(epochs_range, val_acc, label="Val Accuracy", linewidth=2)
        ax1.axvline(x=len(history1.history["accuracy"]), color="gray",
                    linestyle="--", alpha=0.5, label="Fine-tune start")
        ax1.set_title("Model Accuracy", fontsize=14, fontweight="bold")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Accuracy")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Loss
        ax2.plot(epochs_range, loss, label="Train Loss", linewidth=2)
        ax2.plot(epochs_range, val_loss, label="Val Loss", linewidth=2)
        ax2.axvline(x=len(history1.history["loss"]), color="gray",
                    linestyle="--", alpha=0.5, label="Fine-tune start")
        ax2.set_title("Model Loss", fontsize=14, fontweight="bold")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Loss")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        path = os.path.join(output_dir, "training_curves.png")
        plt.savefig(path, dpi=150)
        plt.close()
        print(f"       Saved: {path}")
    except ImportError:
        print("       [SKIP] matplotlib not installed — skipping plots.")


def _generate_confusion_matrix(model, val_data, class_indices, output_dir):
    """Generate and save confusion matrix."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.metrics import (
            confusion_matrix, classification_report, ConfusionMatrixDisplay,
        )

        # Predictions
        val_data.reset()
        y_pred = model.predict(val_data, verbose=0)
        y_pred_classes = np.argmax(y_pred, axis=1)
        y_true = val_data.classes[:len(y_pred_classes)]

        class_names = list(class_indices.keys())

        # Classification report
        report = classification_report(y_true, y_pred_classes,
                                       target_names=class_names)
        print("\n       Classification Report:")
        print(report)

        report_path = os.path.join(output_dir, "classification_report.txt")
        with open(report_path, "w") as f:
            f.write(report)

        # Confusion matrix plot
        cm = confusion_matrix(y_true, y_pred_classes)
        fig, ax = plt.subplots(figsize=(10, 8))
        disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                                      display_labels=class_names)
        disp.plot(ax=ax, cmap="Greens", xticks_rotation=45)
        ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
        plt.tight_layout()
        path = os.path.join(output_dir, "confusion_matrix.png")
        plt.savefig(path, dpi=150)
        plt.close()
        print(f"       Saved: {path}")

    except ImportError:
        print("       [SKIP] sklearn/matplotlib not installed — skipping confusion matrix.")


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
