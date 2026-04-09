from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# -- Local Imports --
from app.core.config import BASE_DIR
from app.core import model

from app.core.config_loader import get_google_drive_folder_id




router = APIRouter()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))




@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "for Object Detection",
            "message0": "Choose Input Source",
            "message1": "Choose Training Workflow",
            "message2": "Settings and Preferences",
        },
    )


@router.get("/page-config")
def page_config(request: Request):
    return templates.TemplateResponse(
        request,
        "page_config.html",
        {
            "request": request,
            "models": model.list_models(),
            "current_model": model.get_model_name() or "No Model Loaded",
            "load_error": model.MODEL_LOAD_ERROR,
            "page_title":"Configuration",
            "page_subtitle": "Manage Models and Set Inference Parameters",
            "page_status": ""
        },
    )


@router.post("/select-model")
def select_model(model_name: str = Form(...)):
    try:
        model.set_model(model_name)
    except Exception as e:
        print(f"Error loading model: {e}")

    return RedirectResponse(url="/page-config", status_code=303)

@router.get("/inference-uploaded", response_class=HTMLResponse)
def inference_uploaded(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_image.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )

# Serves the page

@router.get("/inference-url", response_class=HTMLResponse)
def inference_url_page(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_url.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )



@router.get("/inference-api", response_class=HTMLResponse)
def inference_url_page(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_api.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )


@router.get("/inference-video", response_class=HTMLResponse)
def inference_video(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_video.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )


@router.get("/inference-rtsp", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_rtsp.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )

@router.get("/inference-webcam", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_webcam.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "message": "",
        },
    )



"""
@router.get("/inference-rtsp", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "inference_rtsp.html",
        {"request": request},
    )
"""
@router.get("/stream/view")
def stream_view_page(request: Request, filename: str, conf: float = 0.25, max_fps: float = 15.0):
    return templates.TemplateResponse(
        request,
        "inference_video_stream.html",
        {
            "request": request,
            "model_name": model.get_model_name() or "No model loaded",
            "filename": filename,
            "conf": conf,
            "max_fps": max_fps,
        },
    )

@router.get("/train-google", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/page_train_google.html",
        {
        "request": request,
         "page_title":"Google Training",
        },
    )

@router.get("/train-local", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "page_title":"Local Training",
         "page_subtitle": "Train on Local Machine",
         "page_status": "Coming Soon"
         },
    )

@router.get("/inference-drone", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "page_title":"Drone Inference",
         "page_subtitle": "Infer Drone Freed Data",
         "page_status": "Coming Soon"
         },
    )

@router.get("/page-webhook", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "page_title":"Webhooks",
         "page_subtitle": "",
         "page_status": "Coming Soon"
         },
    )

@router.get("/page-option", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "page_title":"Options",
         "page_subtitle": "",
         "page_status": "Coming Soon"
         },
    )

@router.get("/page-webhook", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "page_title":"Options",
         "page_subtitle": "",
         "page_status": "Coming Soon"
         },
    )


@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/googledrivefolder")
def some_route():
    folder_id = get_google_drive_folder_id()
    # use folder_id
    return {"folder_id": folder_id}


@router.get("/coming-soon", response_class=HTMLResponse)
def inference_rtsp(request: Request):
    return templates.TemplateResponse(
        request,
        "/coming_soon.html",
        {"request": request,
         "message": "This page is coming soon",
         },
    )


# Handle common browser errors that I want to silence
from fastapi import Response

#@router.get("/.well-known/appspecific/com.chrome.devtools.json")
#def chrome_devtools_probe():
#    return Response(status_code=204)



from fastapi.responses import JSONResponse

@router.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools_probe():
    return JSONResponse({})
