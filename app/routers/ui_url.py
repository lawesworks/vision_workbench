from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Request,  Form
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

from app.core import model




# run inference from URL

@router.post("/infer-url", response_class=HTMLResponse)
def infer_url(request: Request, image_url: str = Form(...)):
    # 1) Ensure model is loaded
    if model.MODEL is None:
        return templates.TemplateResponse(
        request,
        "inference_url.html",
            {
                "request": request,
                "uploaded_url": None,
                "annotated_url": None,
                "detections": [],
                "class_counts": {},
                "model_name": model.get_model_name() or "No model loaded",
                "message": MODEL_LOAD_ERROR or "Model not loaded.",
                "status": "danger",
            },
            status_code=500,
        )

    # 2) Validate URL
    url = (image_url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return templates.TemplateResponse(
        request,
        "inference_url.html",
            {
                "request": request,
                "uploaded_url": None,
                "annotated_url": None,
                "detections": [],
                "class_counts": {},
                "model_name": model.get_model_name() or "No model loaded",
                "message": "Please enter a valid http(s) URL.",
                "status": "processing",
            },
            status_code=400,
        )

    # 3) Prepare paths
    uid = uuid4().hex
    download_path = UPLOADS_DIR / f"{uid}.download"

    # 4) Download (streaming) with basic safety limits + headers
    MAX_BYTES = 15 * 1024 * 1024  # 15 MB cap

    parsed = urlparse(url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        # Some hosts require a Referer to prevent hotlinking/bots
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()

                total = 0
                with download_path.open("wb") as f:
                    for chunk in resp.iter_bytes():
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise ValueError(f"File too large (> {MAX_BYTES} bytes).")
                        f.write(chunk)

        # 5) Verify it's actually an image
        head = download_path.read_bytes()[:4096]
        kind = imghdr.what(None, h=head)
        if kind is None:
            download_path.unlink(missing_ok=True)
            raise ValueError("URL did not return a recognizable image.")

        final_path = UPLOADS_DIR / f"{uid}.{kind}"
        download_path.rename(final_path)

    except Exception as e:
        # Cleanup temp file if present
        try:
            download_path.unlink(missing_ok=True)
        except Exception:
            pass

        return templates.TemplateResponse(
        request,
        "inference_url.html",
            {
                "request": request,
                "uploaded_url": None,
                "annotated_url": None,
                "detections": [],
                "class_counts": {},
                "model_name": model.get_model_name() or "No model loaded",
                "message": f"Failed to download image: {e}",
                "status": "danger",
            },
            status_code=400,
        )

    # 6) Run inference
    uploaded_url = f"/static/uploads/{final_path.name}"
    annotated_url, detections, class_counts = run_inference_on_image(
        image_path=final_path,
        uid=uid,
        conf=0.25,
    )

    # 7) Render result
    return templates.TemplateResponse(
        "inference_url.html",
        {
            "request": request,
            "uploaded_url": uploaded_url,
            "annotated_url": annotated_url,
            "detections": detections,
            "class_counts": class_counts,
            "model_name": model.get_model_name() or "No model loaded",
            "message": f"Inference complete ({len(detections)} detections)",
            "url":url,
            "status": "success",
        },
    )