
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
OUTPUTS_DIR = STATIC_DIR / "outputs"
MODELS_DIR = BASE_DIR.parent / "models"

MODEL_CONFIG_FILE = BASE_DIR.parent / "yolo_config.json"

CONFIG_FILE = BASE_DIR.parent / "auth/secrets.json"
GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR.parent / "auth/service-account.json"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# Set this to your weights path. 
WEIGHTS_FILENAME = "" # Default
YOLO_WEIGHTS = Path(os.getenv("YOLO_WEIGHTS", str((BASE_DIR.parent.parent/ "models" / f"{WEIGHTS_FILENAME}").resolve())))
