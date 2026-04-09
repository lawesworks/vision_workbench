from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2


router = APIRouter()

# -- Local Imports --
from app.core.config import UPLOADS_DIR
from app.core.model import MODEL, MODEL_LOAD_ERROR

from app.core import model

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}

def get_video_information(path):
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {path}")

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if not fps or fps <= 1:
        fps = 30
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()
    return fps, frame_count, width, height



@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video format.")

    safe_name = f"{uuid4().hex}{suffix}"
    save_path = UPLOADS_DIR / safe_name

    

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    # Now it's safe to evaluate the file
    try:
        fps_in, frame_count, width, height = get_video_information(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {e}")


    return {
        "fps_in": float(fps_in) if fps_in else None,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "message": "Upload successful",
        "filename": safe_name,
        "original_filename": file.filename
    }
