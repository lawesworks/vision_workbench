from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import httpx
import imghdr
from urllib.parse import urlparse

# -- Local Imports --
from app.core.config import BASE_DIR, UPLOADS_DIR
from app.core.model import MODEL, MODEL_LOAD_ERROR
from app.services.local_inference import run_inference_on_image

router = APIRouter()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# run inference on image using API

"""
### API call for image
curl -s -X POST "http://127.0.0.1:8000/api/infer-image" \
  -F "file=@/path/to/image.jpg" | python -m json.tool
"""

@router.post("/api/infer-image")
def api_infer_image(file: UploadFile = File(...)):
    if MODEL is None:
        raise HTTPException(status_code=500, detail=MODEL_LOAD_ERROR or "Model not loaded.")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid content-type: {file.content_type}")

    ext = Path(file.filename).suffix.lower() or ".jpg"
    uid = uuid4().hex
    upload_name = f"{uid}{ext}"
    upload_path = UPLOADS_DIR / upload_name

    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    uploaded_url = f"/static/uploads/{upload_name}"

    annotated_url, detections, class_counts = run_inference_on_image(
        image_path=upload_path,
        uid=uid,
        conf=0.25,
    )

    return {
        "uploaded_url": uploaded_url,
        "annotated_url": annotated_url,
        "detections": detections,
        "class_counts": class_counts,
    }