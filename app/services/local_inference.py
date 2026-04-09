
from pathlib import Path
import cv2

# -- Local Imports --
from app.core.model import MODEL
from app.core.config import OUTPUTS_DIR

from app.core import model

# -- Run Inference on local image --

def run_inference_on_image(image_path: Path, uid: str, conf: float = 0.25):
    """
    Runs YOLO inference on a local image file, saves an annotated JPG,
    and returns (annotated_url, detections, class_counts).
    """
    results = model.MODEL.predict(source=str(image_path), conf=conf, verbose=False)
    r0 = results[0]

    detections = []
    class_counts = {}

    if r0.boxes is not None and len(r0.boxes) > 0:
        xyxy = r0.boxes.xyxy.cpu().numpy()
        confs = r0.boxes.conf.cpu().numpy()
        clss = r0.boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), c, cls_id in zip(xyxy, confs, clss):
            cls_name = r0.names.get(int(cls_id), str(int(cls_id)))
            detections.append({
                "class_id": int(cls_id),
                "class_name": cls_name,
                "confidence": float(c),
                "box_xyxy": [float(x1), float(y1), float(x2), float(y2)],
            })
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

    annotated_bgr = r0.plot()
    annotated_name = f"{uid}_annotated.jpg"
    annotated_path = OUTPUTS_DIR / annotated_name

    import cv2
    cv2.imwrite(str(annotated_path), annotated_bgr)

    annotated_url = f"/static/outputs/{annotated_name}"
    return annotated_url, detections, class_counts