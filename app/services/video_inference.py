from pathlib import Path
from collections import defaultdict
import cv2

from app.core import model
from app.core.config import OUTPUTS_DIR


def get_video_info(path):
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30.0

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()
    return float(fps), frame_count, width, height


def run_inference_on_video(
    video_path: Path,
    uid: str,
    conf: float = 0.25,
    max_frames: int | None = None,
):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    fps_in, frame_count, width, height = get_video_info(video_path)

    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError("Could not read video dimensions.")

    out_name = f"{uid}_annotated.mp4"
    out_path = OUTPUTS_DIR / out_name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, float(fps_in), (width, height))
    if not writer.isOpened():
        cap.release()
        raise ValueError("Failed to open video writer (codec issue).")

    class_counts = defaultdict(int)
    frames_read = 0
    frames_written = 0

    try:
        while True:
            if max_frames is not None and frames_read >= max_frames:
                break

            ok, frame = cap.read()
            if not ok:
                print(f"DEBUG: cap.read() failed after {frames_read} frames")
                break

            frames_read += 1

            results = model.MODEL.predict(source=frame, conf=conf, verbose=False)
            r0 = results[0]

            if r0.boxes is not None and len(r0.boxes) > 0:
                clss = r0.boxes.cls.cpu().numpy().astype(int)
                for cls_id in clss:
                    cls_name = r0.names.get(int(cls_id), str(int(cls_id)))
                    class_counts[cls_name] += 1

            annotated_bgr = r0.plot()
            writer.write(annotated_bgr)
            frames_written += 1

    finally:
        cap.release()
        writer.release()

    source_duration_est = (frame_count / fps_in) if fps_in and frame_count > 0 else None
    output_duration_est = (frames_written / fps_in) if fps_in and frames_written > 0 else None

    print(f"DEBUG: fps_in={fps_in}")
    print(f"DEBUG: source frame_count metadata={frame_count}")
    print(f"DEBUG: frames_read={frames_read}")
    print(f"DEBUG: frames_written={frames_written}")
    print(f"DEBUG: source_duration_est={source_duration_est}")
    print(f"DEBUG: output_duration_est={output_duration_est}")
    print(f"DEBUG: out_path={out_path}")

    annotated_url = f"/static/outputs/{out_name}"
    summary = {
        "frames_read": frames_read,
        "frames_written": frames_written,
        "fps_in": fps_in,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "class_counts": dict(class_counts),
        "source_duration_estimate_sec": source_duration_est,
        "output_duration_estimate_sec": output_duration_est,
    }
    return annotated_url, summary