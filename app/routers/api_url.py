
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, UploadFile, Request, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import httpx
import imghdr
from urllib.parse import urlparse

# -- Local Imports --
from app.core.config import BASE_DIR, UPLOADS_DIR
from app.core.model import MODEL, MODEL_LOAD_ERROR
from app.services.local_inference import run_inference_on_image
from app.services.url_handlers import download_image

router = APIRouter()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# run inference on url using API

"""
### API call for URL
curl -s -X POST "http://127.0.0.1:8000/api/infer-url" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg"}' \
  | python -m json.tool
"""

@router.post("/api/infer-url")
def api_infer_url(payload: dict = Body(...)):
    if MODEL is None:
        raise HTTPException(status_code=500, detail=MODEL_LOAD_ERROR or "Model not loaded.")

    url = (payload.get("url") if isinstance(payload, dict) else None) or ""
    uid = uuid4().hex

    try:
        final_path = download_image(url=url, dest_dir=UPLOADS_DIR, uid=uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    uploaded_url = f"/static/uploads/{final_path.name}"

    annotated_url, detections, class_counts = run_inference_on_image(
        image_path=final_path,
        uid=uid,
        conf=0.25,
    )

    return {
        "uploaded_url": uploaded_url,
        "annotated_url": annotated_url,
        "detections": detections,
        "class_counts": class_counts,
    }