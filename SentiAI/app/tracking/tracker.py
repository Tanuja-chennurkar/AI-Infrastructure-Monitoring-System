from typing import List, Dict, Any
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from app.core.logging import logger

class DeepSortTracker:
    """Wrapper class for DeepSORT object tracking."""
    def __init__(
        self,
        max_age: int = 30,
        n_init: int = 3,
        nms_max_overlap: float = 1.0,
        max_cosine_distance: float = 0.2,
        embedder: str = "mobilenet"
    ) -> None:
        logger.info("Initializing DeepSORT tracker with MobileNet embedder...")
        try:
            self.tracker = DeepSort(
                max_age=max_age,
                n_init=n_init,
                nms_max_overlap=nms_max_overlap,
                max_cosine_distance=max_cosine_distance,
                embedder=embedder,
                half=False  # Keep false on CPU for compatibility
            )
            logger.info("DeepSORT tracker initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing DeepSORT tracker: {e}")
            raise e

    def update(self, detections: List[Dict[str, Any]], frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Updates the tracker with YOLOv8 detections.
        
        detections format: [
            {"box": [x1, y1, x2, y2], "confidence": float, "class_id": int, "class_name": str}
        ]
        
        Returns tracked objects: [
            {
                "track_id": str,
                "box": [x1, y1, x2, y2],
                "class_id": int,
                "class_name": str
            }
        ]
        """
        formatted_detections = []
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            w = x2 - x1
            h = y2 - y1
            # DeepSORT format: ([left, top, w, h], confidence, detection_class)
            formatted_detections.append(([x1, y1, w, h], det["confidence"], det["class_name"]))

        try:
            tracks = self.tracker.update_tracks(formatted_detections, frame=frame)
            tracked_objects = []

            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                # to_ltrb() returns [left, top, right, bottom]
                ltrb = track.to_ltrb()
                class_name = track.get_det_class()
                
                tracked_objects.append({
                    "track_id": str(track_id),
                    "box": [int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])],
                    "class_name": class_name
                })

            return tracked_objects
        except Exception as e:
            logger.error(f"Error updating DeepSORT tracker: {e}")
            return []
