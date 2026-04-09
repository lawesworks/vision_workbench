from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates

# -- Local Imports --
from app.core.config import BASE_DIR, UPLOADS_DIR
from app.core.model import MODEL, MODEL_LOAD_ERROR
from app.services.video_inference import run_inference_on_video

router = APIRouter()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# run inference on video using API

"""
### API call for video inference
curl -s -X POST "http://127.0.0.1:8000/api/infer-video?max_frames=200&conf=0.25" \
-F "file=@/Users/bernard/Documents/Data/Sample/images/cars.mp4" \
| python -m json.tool
"""

@router.post("/api/infer-video")
def api_infer_video(
    file: UploadFile = File(...),
    max_frames: int = 200,
    conf: float = 0.25,
):
    if MODEL is None:
        raise HTTPException(status_code=500, detail=MODEL_LOAD_ERROR or "Model not loaded.")

    # Basic guard; browsers sometimes send video/*, but some send application/octet-stream
    #if file.content_type and not file.content_type.startswith("video/"):
    #    raise HTTPException(status_code=400, detail=f"Invalid content-type: {file.content_type}")

    allowed_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    ext = Path(file.filename).suffix.lower()

    if file.content_type:
        ct = file.content_type.lower()
        if ct.startswith("video/"):
            pass
        elif ct == "application/octet-stream" and ext in allowed_exts:
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Invalid content-type: {file.content_type}")
    else:
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Missing content-type and unknown video extension.")

    uid = uuid4().hex
    ext = Path(file.filename).suffix.lower() or ".mp4"
    upload_name = f"{uid}{ext}"
    upload_path = UPLOADS_DIR / upload_name

    # Save uploaded video
    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    uploaded_url = f"/static/uploads/{upload_name}"

    try:
        annotated_url, summary = run_inference_on_video(
            video_path=upload_path,
            uid=uid,
            conf=conf,
            max_frames=max_frames,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "uploaded_url": uploaded_url,
        "annotated_url": annotated_url,
        "summary": summary,
    }
