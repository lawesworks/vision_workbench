
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# -- Local Imports --
from app.core.config import BASE_DIR, UPLOADS_DIR
from app.core.model import MODEL_LOAD_ERROR
from app.services.local_inference import run_inference_on_image

router = APIRouter()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

from app.core import model



@router.post("/upload-image", response_class=HTMLResponse)
def upload_image(request: Request, file: UploadFile = File(...)):
    model_name = model.get_model_name() or "No model loaded"
    if not file.content_type or not file.content_type.startswith("image/"):
        return templates.TemplateResponse(
        request,
        "inference_image.html",
            {
                "request": request,
                "uploaded_url": None,
                "annotated_url": None,
                "detections": [],
                "class_counts": {},
                "model_name": model_name,
                "message": f"That doesn't look like an image (content-type: {file.content_type}).",
            },
            status_code=400,
        )

    if model.MODEL is None:
        return templates.TemplateResponse(
        request,
        "inference_image.html",
            {
                "request": request,
                "uploaded_url": None,
                "annotated_url": None,
                "detections": [],
                "class_counts": {},
                "model_name": model_name,
                "message": MODEL_LOAD_ERROR or "Model not loaded.",
            },
            status_code=500,
        )

    # 1) Save upload
    ext = Path(file.filename).suffix.lower() or ".jpg"
    uid = uuid4().hex
    upload_name = f"{uid}{ext}"
    upload_path = UPLOADS_DIR / upload_name

    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    uploaded_url = f"/static/uploads/{upload_name}"

    # 4️Run inference using helper function
    annotated_url, detections, class_counts = run_inference_on_image(
        image_path=upload_path,
        uid=uid,
        conf=0.25
    )

    return templates.TemplateResponse(
        request,
        "inference_image.html",
        {
            "request": request,
            "uploaded_url": uploaded_url,
            "annotated_url": annotated_url,
            "detections": detections,
            "class_counts": class_counts,
            "model_name": model_name,
            "message": f"Inference complete ({len(detections)} detections) [Image]",
        },
    )