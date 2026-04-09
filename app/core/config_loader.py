import json
from pathlib import Path

# -- Local Imports --
from app.core.config import CONFIG_FILE

CONFIG_PATH = CONFIG_FILE


import logging

logger = logging.getLogger("uvicorn.error")




# -- Auto-Generate Default Files that were not sent to GitHub -- #
def ensure_json_file_exists(file_path: Path, default_data: dict):
    if not file_path.exists():
        logger.warning(f"{file_path} not found.  Creating a dummy file using that name")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(default_data, f, indent=2)



ensure_json_file_exists(
    Path("auth/secrets.json"),
    {"google_drive_folder_id": ""}
)

ensure_json_file_exists(
    Path("auth/service-account.json"),
    {"type": "service_account"}
)




def load_config():
    if not CONFIG_PATH.exists():
        logger.warning("auth/secrets.json was not found.  Returning a dummy JSON")
        return {"dummy_key": "dummy_value"}

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def get_google_drive_folder_id():
    secrets = load_config()
    folder_id = secrets.get("google_drive_folder_id", "")

    if not folder_id:
        logger.warning("Google Drive Folder ID not found. Please update auth/secrets.json")
        return ""

    return folder_id





