from pathlib import Path
from fastapi import APIRouter, HTTPException
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pydantic import BaseModel

import json
import os
import tempfile

from app.core.config import BASE_DIR

from app.core.config_loader import get_google_drive_folder_id
from app.core.config import MODEL_CONFIG_FILE
from app.core.config import GOOGLE_SERVICE_ACCOUNT_FILE

router = APIRouter()

import logging
logger = logging.getLogger("uvicorn.error")


GOOGLE_MODEL_CONFIG_FILENAME  = MODEL_CONFIG_FILE 
GOOGLE_SERVICE_ACCOUNT_PATH   = GOOGLE_SERVICE_ACCOUNT_FILE
GOOGLE_SERVICE_ACCOUNT_SCOPES = ["https://www.googleapis.com/auth/drive"]
GOOGLE_DRIVE_FOLDER_ID        = get_google_drive_folder_id() 



def get_drive_service():
    if not GOOGLE_SERVICE_ACCOUNT_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Service account file not found: {GOOGLE_SERVICE_ACCOUNT_PATH}"
        )

    try:
        creds = Credentials.from_service_account_file(
            str(GOOGLE_SERVICE_ACCOUNT_PATH),
            scopes=GOOGLE_SERVICE_ACCOUNT_SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Drive auth error: {type(e).__name__}: {str(e)}"
        )


def find_existing_file(service, filename: str, folder_id: str):
    try:
        query = (
            f"name = '{filename}' "
            f"and '{folder_id}' in parents "
            f"and trashed = false"
        )

        results = service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        return files[0] if files else None

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Drive search error: {type(e).__name__}: {str(e)}"
        )


@router.post("/drive/upload-config")
def upload_config(project_url: str = None, dataset_version: int = None):

    print("3222424")

    if not GOOGLE_DRIVE_FOLDER_ID:
        #raise RuntimeError("Google Drive folder ID is required for this operation")
        logger.warning(f"Google Drive Folder ID was not found and required for this operation")
        return {
                    "status": "failed",
                    "info": "Google Drive Folder ID was not found and required for this operation"
                }

    service = get_drive_service()

    message = "Config Upload Started..."



    data = {
        "Roboflow_Project_URL": project_url,
        "Roboflow_Dataset_Version": dataset_version
    }

    tmp_path = None



    try:
        model_config_basename = os.path.basename(GOOGLE_MODEL_CONFIG_FILENAME)
        existing_file = find_existing_file(
            service=service,
            filename=model_config_basename,#"roboflow_config.json",
            folder_id=GOOGLE_DRIVE_FOLDER_ID
        )

        if not existing_file:
            print("\n"+ model_config_basename + " was not found in the target Drive folder. "
                    "Create it manually once within the drive, then this route can update it.\n")
            raise HTTPException(
                status_code=500,
                detail=("f{model_config_basename}was not found in the target Drive folder. "
                    "Create it manually once within the drive, then this route can update it."
                )
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name

        media = MediaFileUpload(tmp_path, mimetype="application/json")

        message ="Successfully updated "+ model_config_basename
        updated_file = service.files().update(
            fileId=existing_file["id"],
            media_body=media,
            fields="id,name"
        ).execute()

        return {
            "status": "ok",
            "info": "Google Drive File Update was successful",
            "url":project_url,
            "version":message,
            "file_id": updated_file["id"],
            "file_name": updated_file["name"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Drive upload error: {type(e).__name__}: {str(e)}"
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)






class TrainConfig(BaseModel):
    project_url: str
    dataset_version: int
    yolo_version: str
    yolo_size: str
    epochs: int
    batches: int
    learning_rate: float
    image_size: int
    #roboflow_api_key: str


@router.post("/config/save")
def save_config(config: TrainConfig):
    data = {
        "Roboflow_Project_URL": config.project_url,
        "Roboflow_Dataset_Version": config.dataset_version,
        "YOLO_Version": config.yolo_version,
        "YOLO_Size": config.yolo_size,
        "Epochs": config.epochs,
        "Batches": config.batches,
        "Learning_Rate": config.learning_rate,
        "Image_Size": config.image_size,
        #"Roboflow_API_Key": config.roboflow_api_key
    }

    with open(MODEL_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "success", "message": "Config saved"}



class RoboflowConfigResponse(BaseModel):
    Roboflow_Project_URL: str
    Roboflow_Dataset_Version: int
    YOLO_Version: str
    YOLO_Size: str
    Config_Epochs: int
    Config_Batches: int
    Config_Learning_Rate: float
    Config_Image_Size: int
    #Roboflow_API_Key: str



@router.get("/roboflow-config", response_model=RoboflowConfigResponse)
def get_roboflow_config():
    if not MODEL_CONFIG_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Config file not found: {MODEL_CONFIG_FILE}"
        )

    try:
        with open(MODEL_CONFIG_FILE, "r") as f:
            cfg = json.load(f)

        return {
            "Roboflow_Project_URL": cfg["Roboflow_Project_URL"],
            "Roboflow_Dataset_Version": cfg["Roboflow_Dataset_Version"],
            "YOLO_Version": cfg["YOLO_Version"],
            "YOLO_Size": cfg["YOLO_Size"],
            "Config_Epochs": cfg["Epochs"],
            "Config_Batches": cfg["Batches"],
            "Config_Learning_Rate": cfg["Learning_Rate"],
            "Config_Image_Size": cfg["Image_Size"],
            #"Roboflow_API_Key": cfg["Roboflow_API_Key"],
            #"Roboflow_API_Key": "*" * len(cfg["Roboflow_API_Key"]),
        }

    except KeyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Missing config key: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    