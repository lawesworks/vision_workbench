from __future__ import annotations

import time
from typing import Generator

import cv2
import numpy as np

from app.core import model


def _build_mjpeg_chunk(jpg_bytes: bytes) -> bytes:
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"
    )


def _yield_error_frame(message: str) -> Generator[bytes, None, None]:
    frame = np.zeros((480, 900, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        message,
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 255),
        3,
    )

    ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if ok:
        yield _build_mjpeg_chunk(jpg.tobytes())


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_capture_fps(cap: "cv2.VideoCapture") -> float:
    fps = _safe_float(cap.get(cv2.CAP_PROP_FPS), 0.0)
    if fps <= 1.0 or fps > 240.0:
        return 0.0
    return fps


def _choose_stream_fps(
    cap: "cv2.VideoCapture",
    max_fps: float,
    respect_source_fps: bool,
) -> float:
    """
    Decide how fast to pace the MJPEG stream.

    - For file uploads, respect source FPS but cap at max_fps.
    - For live sources (webcam / RTSP), just use max_fps.
    """
    max_fps = _safe_float(max_fps, 15.0)
    if max_fps <= 0:
        max_fps = 15.0

    if respect_source_fps:
        source_fps = _get_capture_fps(cap)
        if source_fps > 0:
            return min(source_fps, max_fps)

    return max_fps




def mjpeg_stream_from_capture(
    cap: "cv2.VideoCapture",
    conf: float = 0.25,
    max_fps: float = 15.0,
    respect_source_fps: bool = False,
) -> Generator[bytes, None, None]:
    """
    Read frames from an OpenCV capture, run YOLO on each frame, and yield MJPEG.

    Args:
        cap: OpenCV VideoCapture instance.
        conf: YOLO confidence threshold.
        max_fps: Maximum MJPEG output FPS.
        respect_source_fps: If True, pace the stream using min(source_fps, max_fps).
                            Best for uploaded video files.
                            If False, pace only by max_fps. Best for live streams.
    """
    if model.MODEL is None:
        yield from _yield_error_frame("MODEL NOT LOADED")
        cap.release()
        return

    stream_fps = _choose_stream_fps(
        cap=cap,
        max_fps=max_fps,
        respect_source_fps=respect_source_fps,
    )
    frame_interval = 1.0 / stream_fps if stream_fps > 0 else 0.0

    try:
        while True:
            loop_start = time.time()

            ok, frame = cap.read()
            if not ok:
                break

            results = model.MODEL.predict(source=frame, conf=conf, verbose=False)
            annotated = results[0].plot()

            ok2, jpg = cv2.imencode(
                ".jpg",
                annotated,
                [int(cv2.IMWRITE_JPEG_QUALITY), 80],
            )
            if not ok2:
                continue

            yield _build_mjpeg_chunk(jpg.tobytes())

            if frame_interval > 0:
                elapsed = time.time() - loop_start
                sleep_time = frame_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    finally:
        cap.release()