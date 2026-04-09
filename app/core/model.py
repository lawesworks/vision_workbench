
"""

import os
from pathlib import Path
from ultralytics import YOLO

# -- Local Imports --
from app.core.config import YOLO_WEIGHTS

# ---- Model config ----

if not YOLO_WEIGHTS.exists():
    # Don't crash hard; let the UI show a helpful message until you add weights.
    MODEL = None
    MODEL_LOAD_ERROR = f"Model weights not found at: {YOLO_WEIGHTS}"
else:
    MODEL = YOLO(str(YOLO_WEIGHTS))
    MODEL_LOAD_ERROR = None

"""

from pathlib import Path
from ultralytics import YOLO
from app.core.config import BASE_DIR

MODELS_DIR = BASE_DIR.parent / "models"

_current_model_name = "yolo-traffic.pt"
MODEL_LOAD_ERROR = None

try:
    MODEL = YOLO(str(MODELS_DIR / _current_model_name))
except Exception as e:
    MODEL = None
    MODEL_LOAD_ERROR = str(e)


def get_model():
    return MODEL


def get_model_name():
    return _current_model_name.removesuffix(".pt")


def list_models():
    return sorted([p.name for p in MODELS_DIR.glob("*.pt")])


def set_model(model_name: str):
    global MODEL, _current_model_name, MODEL_LOAD_ERROR

    model_path = MODELS_DIR / model_name

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_name}")

    if model_path.suffix.lower() != ".pt":
        raise ValueError("Only .pt files are allowed")

    MODEL = YOLO(str(model_path))
    _current_model_name = model_name
    MODEL_LOAD_ERROR = None