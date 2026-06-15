from typing import List, Dict, Any
import numpy as np
from ultralytics import YOLO
from app.core.config import settings
from app.core.logging import logger

# COCO Class IDs of interest
CLASS_MAP = {
    0: "person",
    24: "backpack",
    26: "handbag",
    28: "suitcase"
}

class YOLODetector:
    """Wrapper class for YOLOv8 object detection."""
    def __init__(
        self,
        model_name: str = settings.YOLO_MODEL,
        confidence_threshold: float = settings.CONFIDENCE_THRESHOLD
    ) -> None:
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        logger.info(f"Initializing YOLOv8 model: {self.model_name} with threshold: {self.confidence_threshold}")
        try:
            self.model = YOLO(self.model_name)
            logger.info("YOLOv8 model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading YOLOv8 model: {e}")
            raise e

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs inference on the frame and returns detections for classes of interest.
        Returns a list of dicts: [
            {
                "box": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": int,
                "class_name": str
            }
        ]
        """
        if frame is None:
            return []

        try:
            # Run inference; verbose=False to clean up console logs
            results = self.model(frame, verbose=False)
            detections = []

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    conf = float(box.conf[0].cpu().numpy())
                    if conf < self.confidence_threshold:
                        continue

                    class_id = int(box.cls[0].cpu().numpy())
                    # Only keep person and bags (backpack, handbag, suitcase)
                    if class_id in CLASS_MAP:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detections.append({
                            "box": [int(x1), int(y1), int(x2), int(y2)],
                            "confidence": conf,
                            "class_id": class_id,
                            "class_name": CLASS_MAP[class_id]
                        })

            return detections
        except Exception as e:
            logger.error(f"Error during YOLOv8 inference: {e}")
            return []
