from __future__ import annotations

import os

import cv2
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core import model
from app.core.config import UPLOADS_DIR
from app.services.stream_handlers import mjpeg_stream_from_capture

router = APIRouter()


def _multipart_stream_response(generator):
    return StreamingResponse(
        generator,
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


def _open_file_capture(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Failed to open video.")
    return cap


def _open_rtsp_capture(url: str):
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise HTTPException(
            status_code=400,
            detail="Failed to open stream. Check URL/network/credentials.",
        )
    return cap


def _open_webcam_capture(index: int):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise HTTPException(
            status_code=400,
            detail=f"Failed to open webcam index {index}.",
        )
    return cap




ACTIVE_CAPTURES = {}

def register_capture(index: int, cap):
    old_cap = ACTIVE_CAPTURES.get(index)
    if old_cap is not None and old_cap is not cap:
        old_cap.release()

    ACTIVE_CAPTURES[index] = cap


def unregister_capture(index: int, cap):
    current = ACTIVE_CAPTURES.get(index)
    if current is cap:
        ACTIVE_CAPTURES.pop(index, None)


def stop_webcam_capture(index: int) -> bool:
    cap = ACTIVE_CAPTURES.get(index)
    if cap is None:
        return False

    try:
        cap.release()
    finally:
        ACTIVE_CAPTURES.pop(index, None)

    return True






@router.get("/stream/uploaded")
def stream_uploaded_video(
    filename: str,
    conf: float = 0.25,
    max_fps: float = 15.0,
):
    video_path = (UPLOADS_DIR / filename).resolve()

    if UPLOADS_DIR.resolve() not in video_path.parents:
        raise HTTPException(status_code=400, detail="Invalid filename/path.")

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found.")

    cap = _open_file_capture(video_path)

    return _multipart_stream_response(
        mjpeg_stream_from_capture(
            cap=cap,
            conf=conf,
            max_fps=max_fps,
            respect_source_fps=True,
        )
    )


@router.get("/stream/rtsp")
def stream_rtsp(
    url: str,
    conf: float = 0.25,
    max_fps: float = 15.0,
):
    if not (
        url.startswith("rtsp://")
        or url.startswith("rtsps://")
        or url.startswith("http://")
        or url.startswith("https://")
    ):
        raise HTTPException(
            status_code=400,
            detail="URL must be rtsp(s) or http(s).",
        )

    cap = _open_rtsp_capture(url)

    return _multipart_stream_response(
        mjpeg_stream_from_capture(
            cap=cap,
            conf=conf,
            max_fps=max_fps,
            respect_source_fps=False,
        )
    )


@router.get("/stream/webcam")
async def stream_webcam(
    request: Request,
    index: int = 0,
    conf: float = 0.25,
    max_fps: float = 15.0,
):
    if model.MODEL is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")

    cap = _open_webcam_capture(index)

    # Register this exact capture so /stop-webcam can release it later
    register_capture(index, cap)

    def stream_generator():
        try:
            yield from mjpeg_stream_from_capture(
                cap=cap,
                conf=conf,
                max_fps=max_fps,
                respect_source_fps=False,
            )
        finally:
            # Always release on exit
            try:
                cap.release()
            finally:
                unregister_capture(index, cap)

    return _multipart_stream_response(stream_generator())


@router.post("/stop-webcam")
def stop_webcam(index: int):
    stopped = stop_webcam_capture(index)
    return {"stopped": stopped, "index": index}
