import os
import cv2
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.database.models import EventModel, AlertModel
from app.detection.detector import YOLODetector
from app.tracking.tracker import DeepSortTracker
from app.events.engine import EventEngine
import uuid

def format_offset(seconds: float) -> str:
    secs = int(seconds)
    mins = secs // 60
    hours = mins // 60
    return f"{hours:02d}:{mins%60:02d}:{secs%60:02d}"

class VideoPipelineManager:
    """Manages the video acquisition, detection, tracking, and event engine loop in a background thread."""
    
    def __init__(self) -> None:
        self.stream_source = settings.VIDEO_SOURCE
        self.is_active = False
        self._thread: Optional[threading.Thread] = None
        
        # Core ML/Tracking engines (initialized lazily to speed up startup)
        self.detector: Optional[YOLODetector] = None
        self.tracker: Optional[DeepSortTracker] = None
        self.event_engine = EventEngine()
        
        # Thread safety frame buffer
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        
        # Performance/Status metrics
        self.fps = 0.0
        self.frame_count = 0
        self.start_time: Optional[float] = None

        # --- NEW METADATA FOR RUNS & REPORTS ---
        self.run_uuid: Optional[str] = None
        self.run_start_time: Optional[datetime] = None
        self.run_events: List[Dict[str, Any]] = []
        self.run_alerts: List[Dict[str, Any]] = []
        self.run_keyframes: List[Dict[str, Any]] = []
        self.keyframe_index = 0
        
        # Tracked entities sets (for metrics)
        self.tracked_persons: Set[str] = set()
        self.tracked_bags: Set[str] = set()
        self.tracked_vehicles: Set[str] = set()
        
        # Entry/exit tracking
        self.person_first_seen: Dict[str, datetime] = {}
        self.person_last_seen: Dict[str, datetime] = {}
        
    def get_status(self) -> Dict[str, Any]:
        """Returns the status details of the video stream pipeline."""
        return {
            "is_running": self.is_active,
            "source": self.stream_source,
            "fps": round(self.fps, 1),
            "processed_frames": self.frame_count,
            "uptime_seconds": int(time.time() - self.start_time) if self.start_time else 0,
            "run_uuid": self.run_uuid
        }

    def get_current_frame_jpeg(self) -> Optional[bytes]:
        """Encodes and returns the latest processed frame in JPEG format."""
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self._latest_frame)
            if ret:
                return jpeg.tobytes()
            return None

    def start(self, source: Optional[str] = None) -> bool:
        """Starts the video pipeline background thread."""
        if self.is_active:
            logger.warning("Pipeline is already running.")
            return False
            
        if source:
            self.stream_source = source
            
        self.is_active = True
        self.start_time = time.time()
        self.frame_count = 0
        
        # --- RESET RUN METADATA ---
        self.run_uuid = str(uuid.uuid4())
        self.run_start_time = datetime.utcnow()
        self.run_events = []
        self.run_alerts = []
        self.run_keyframes = []
        self.keyframe_index = 0
        
        self.tracked_persons = set()
        self.tracked_bags = set()
        self.tracked_vehicles = set()
        
        self.person_first_seen = {}
        self.person_last_seen = {}
        
        self._thread = threading.Thread(target=self._run_pipeline, daemon=True)
        self._thread.start()
        logger.info(f"Video pipeline thread started with source: {self.stream_source}")
        return True

    def stop(self) -> bool:
        """Stops the video pipeline background thread."""
        if not self.is_active:
            logger.warning("Pipeline is not running.")
            return False
            
        self.is_active = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
            
        # Save final report on manual stop
        try:
            self.save_report()
        except Exception as rep_err:
            logger.error(f"Failed to save report: {rep_err}")
            
        logger.info("Video pipeline stopped.")
        return True

    def _run_pipeline(self) -> None:
        """Main pipeline loop executing detection, tracking, and rules."""
        db = SessionLocal()
        
        # Check if source is mock
        is_mock = (self.stream_source.lower() == "mock")
        
        # Initialize ML modules only if not using mock source
        if not is_mock:
            try:
                if self.detector is None:
                    self.detector = YOLODetector()
                if self.tracker is None:
                    self.tracker = DeepSortTracker()
            except Exception as e:
                logger.error(f"Failed to initialize ML models. Falling back to mock feed. Error: {e}")
                is_mock = True
                
        cap = None
        if not is_mock:
            # Parse source (int for webcam index, str for file path/stream)
            src: Any = self.stream_source
            if src.isdigit():
                src = int(src)
            cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                logger.error(f"Could not open OpenCV video source: {self.stream_source}. Falling back to mock.")
                is_mock = True

        # For FPS calculation
        t_start = time.time()
        
        # Simulated states for mock source
        mock_person_x = 50
        mock_person_y = 200
        mock_person_direction = 1
        mock_track_id = "101"
        mock_bag_track_id = "202"
        
        while self.is_active:
            frame_start_time = time.time()
            timestamp = datetime.utcnow()
            
            detections = []
            tracked_objects = []
            raw_frame = None

            if is_mock:
                # Generate a premium high-tech visualization canvas
                raw_frame = np.zeros((settings.FRAME_HEIGHT, settings.FRAME_WIDTH, 3), dtype=np.uint8)
                
                # Draw grid lines for high-tech look
                for grid_x in range(0, settings.FRAME_WIDTH, 80):
                    cv2.line(raw_frame, (grid_x, 0), (grid_x, settings.FRAME_HEIGHT), (20, 20, 30), 1)
                for grid_y in range(0, settings.FRAME_HEIGHT, 80):
                    cv2.line(raw_frame, (grid_y, 0), (settings.FRAME_WIDTH, grid_y), (20, 20, 30), 1)
                
                # Mock moving person
                mock_person_x += mock_person_direction * 2
                if mock_person_x > 450 or mock_person_x < 50:
                    mock_person_direction *= -1
                
                # Populate mock person detection and track
                p_box = [mock_person_x, mock_person_y, mock_person_x + 100, mock_person_y + 200]
                detections.append({
                    "box": p_box,
                    "confidence": 0.92,
                    "class_id": 0,
                    "class_name": "person"
                })
                tracked_objects.append({
                    "track_id": mock_track_id,
                    "box": p_box,
                    "class_name": "person"
                })
                
                # Populate mock bag (Rule 1: Person carrying bag detected simultaneously)
                # Introduce the bag after 3 seconds of runtime to simulate state changes
                uptime = time.time() - self.start_time if self.start_time else 0
                if uptime > 3.0:
                    b_box = [mock_person_x + 30, mock_person_y + 80, mock_person_x + 70, mock_person_y + 140]
                    detections.append({
                        "box": b_box,
                        "confidence": 0.85,
                        "class_id": 24,
                        "class_name": "backpack"
                    })
                    tracked_objects.append({
                        "track_id": mock_bag_track_id,
                        "box": b_box,
                        "class_name": "backpack"
                    })
                
                # Simulate frame capture timing (approx 30 FPS)
                time.sleep(max(0.01, 0.033 - (time.time() - frame_start_time)))
            else:
                ret, raw_frame = cap.read()
                if not ret:
                    logger.info("Video stream completed. Stopping pipeline...")
                    self.is_active = False
                    break
                
                # Resize for consistency and performance
                raw_frame = cv2.resize(raw_frame, (settings.FRAME_WIDTH, settings.FRAME_HEIGHT))
                
                # ML inference
                detections = self.detector.detect(raw_frame)
                
                # Tracking update
                tracked_objects = self.tracker.update(detections, raw_frame)

            # Draw Visual Annotations on raw_frame first so keyframes have bounding boxes
            annotated_frame = raw_frame.copy()
            
            # Draw standard CCTV header overlay
            cv2.rectangle(annotated_frame, (10, 10), (280, 45), (15, 15, 20), -1)
            cv2.rectangle(annotated_frame, (10, 10), (280, 45), (46, 204, 113), 1)
            cv2.putText(annotated_frame, f"SENTINEL-AI CCTV // SOURCE: {os.path.basename(self.stream_source).upper()}", 
                        (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"TIME: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", 
                        (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (46, 204, 113), 1, cv2.LINE_AA)
            
            # Track unique IDs for metrics and entry/exit
            active_person_ids = set()
            for obj in tracked_objects:
                track_id = obj["track_id"]
                cls_name = obj["class_name"]
                
                # Determine colors (BGR): Neon Cyan for person, Coral for bags
                color = (255, 191, 0) if cls_name == "person" else (80, 127, 255)
                
                # Bounding Box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2) if 'x1' in locals() else None # just in case
                # Actually, let's unpack box from obj
                x1, y1, x2, y2 = obj["box"]
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # Label box tag
                label = f"{cls_name.upper()} ID: {track_id}"
                label_size, base_line = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                y1_label = max(y1, label_size[1] + 10)
                
                cv2.rectangle(annotated_frame, (x1, y1_label - label_size[1] - 4), (x1 + label_size[0] + 6, y1_label + base_line - 2), color, -1)
                cv2.putText(annotated_frame, label, (x1 + 3, y1_label - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

                if cls_name == "person":
                    active_person_ids.add(track_id)
                    self.tracked_persons.add(track_id)
                    
                    if track_id not in self.person_first_seen:
                        self.person_first_seen[track_id] = timestamp
                        self.person_last_seen[track_id] = timestamp
                        
                        # Save person_entry event to DB
                        try:
                            db_entry_event = EventModel(
                                timestamp=timestamp,
                                event_type="person_entry",
                                tracking_id=track_id,
                                source_stream=self.stream_source,
                                details=json.dumps({"message": f"Person ID {track_id} entered scene."})
                            )
                            db.add(db_entry_event)
                            db.commit()
                            
                            self.run_events.append({
                                "timestamp": timestamp,
                                "event_type": "person_entry",
                                "tracking_id": track_id,
                                "details": {"message": f"Person ID {track_id} entered scene."}
                            })
                            # Continually update report
                            try:
                                self.save_report()
                            except Exception as rep_err:
                                logger.error(f"Failed to save report: {rep_err}")
                        except Exception as db_err:
                            db.rollback()
                            logger.error(f"Database write error for entry event: {db_err}")
                    else:
                        self.person_last_seen[track_id] = timestamp
                        
                elif cls_name in {"backpack", "handbag", "suitcase"}:
                    self.tracked_bags.add(track_id)
                elif cls_name in {"car", "motorcycle", "bus", "truck"}:
                    self.tracked_vehicles.add(track_id)
            
            # Check for person_exit events (occluded/gone for > 5.0 seconds)
            expired_pids = []
            for pid, last_seen_time in self.person_last_seen.items():
                if pid not in active_person_ids:
                    if (timestamp - last_seen_time).total_seconds() > 5.0:
                        expired_pids.append(pid)
                        
            for pid in expired_pids:
                duration = int((self.person_last_seen[pid] - self.person_first_seen[pid]).total_seconds())
                try:
                    db_exit_event = EventModel(
                        timestamp=timestamp,
                        event_type="person_exit",
                        tracking_id=pid,
                        source_stream=self.stream_source,
                        details=json.dumps({"message": f"PERSON ID {pid} left scene (Duration: {duration}s)."})
                    )
                    db.add(db_exit_event)
                    db.commit()
                    
                    self.run_events.append({
                        "timestamp": timestamp,
                        "event_type": "person_exit",
                        "tracking_id": pid,
                        "details": {"message": f"PERSON ID {pid} left scene (Duration: {duration}s)."}
                    })
                    # Continually update report
                    try:
                        self.save_report()
                    except Exception as rep_err:
                        logger.error(f"Failed to save report: {rep_err}")
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Database write error for exit event: {db_err}")
                
                self.person_first_seen.pop(pid, None)
                self.person_last_seen.pop(pid, None)

            # Evaluate Event Engine
            engine_results = self.event_engine.evaluate(
                detections, tracked_objects, self.stream_source, timestamp
            )
            
            # Save events and alerts to DB
            if engine_results:
                try:
                    for event_data, alert_data in engine_results:
                        db_event = EventModel(
                            timestamp=timestamp,
                            event_type=event_data["event_type"],
                            tracking_id=event_data["tracking_id"],
                            source_stream=event_data["source_stream"],
                            details=json.dumps(event_data["details"])
                        )
                        db.add(db_event)
                        db.flush()  # Populates id field
                        
                        self.run_events.append({
                            "timestamp": timestamp,
                            "event_type": event_data["event_type"],
                            "tracking_id": event_data["tracking_id"],
                            "details": event_data["details"]
                        })
                        
                        if alert_data:
                            db_alert = AlertModel(
                                timestamp=timestamp,
                                alert_type=alert_data["alert_type"],
                                message=alert_data["message"],
                                event_id=db_event.id,
                                status=alert_data["status"]
                            )
                            db.add(db_alert)
                            
                            self.run_alerts.append({
                                "timestamp": timestamp,
                                "alert_type": alert_data["alert_type"],
                                "message": alert_data["message"]
                            })
                            
                            # Save keyframe screenshot
                            try:
                                keyframe_dir = os.path.join(settings.BASE_DIR, "static", "keyframes")
                                os.makedirs(keyframe_dir, exist_ok=True)
                                self.keyframe_index += 1
                                keyframe_filename = f"keyframe_{self.keyframe_index}_{self.run_uuid}.jpg"
                                keyframe_filepath = os.path.join(keyframe_dir, keyframe_filename)
                                cv2.imwrite(keyframe_filepath, annotated_frame)
                                
                                self.run_keyframes.append({
                                    "url": f"/static/keyframes/{keyframe_filename}",
                                    "timestamp": timestamp,
                                    "index": self.keyframe_index
                                })
                            except Exception as kf_err:
                                logger.error(f"Failed to save keyframe: {kf_err}")
                                
                    db.commit()
                    
                    # Continually update report
                    try:
                        self.save_report()
                    except Exception as rep_err:
                        logger.error(f"Failed to save report: {rep_err}")
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Database write error: {db_err}")
                
            # Update frame buffer
            with self._frame_lock:
                self._latest_frame = annotated_frame
                
            self.frame_count += 1
            
            # Compute real FPS periodically
            if self.frame_count % 30 == 0:
                elapsed = time.time() - t_start
                self.fps = 30.0 / elapsed
                t_start = time.time()

        if cap is not None:
            cap.release()
        db.close()
        logger.info("Pipeline processing loop terminated.")
        
        # Save final report on completion
        try:
            self.save_report()
        except Exception as rep_err:
            logger.error(f"Failed to save report: {rep_err}")

    def save_report(self) -> None:
        """Saves a JSON report for the current run."""
        if not self.run_uuid:
            return
            
        report_dir = os.path.join(settings.BASE_DIR, "static", "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        formatted_events = []
        formatted_alerts = []
        
        # Sort events by timestamp
        self.run_events.sort(key=lambda x: x["timestamp"])
        
        for ev in self.run_events:
            offset_sec = (ev["timestamp"] - self.run_start_time).total_seconds()
            offset_str = format_offset(offset_sec)
            pid = ev["tracking_id"] or "—"
            
            if ev["event_type"] == "person_entry":
                formatted_events.append({
                    "time": offset_str,
                    "type": "PERSON_ENTRY",
                    "id": pid,
                    "log": f"Person ID {pid} entered scene."
                })
            elif ev["event_type"] == "person_exit":
                msg = ev["details"].get("message", f"PERSON ID {pid} left scene.")
                formatted_events.append({
                    "time": offset_str,
                    "type": "PERSON_EXIT",
                    "id": pid,
                    "log": msg
                })
            elif ev["event_type"] == "suspicious_object_presence":
                formatted_events.append({
                    "time": offset_str,
                    "type": "ALERT_TRIGGERED",
                    "id": pid,
                    "log": f"ALERT [MEDIUM]: Intrusion detected: Person ID {pid} entered secure area."
                })
                formatted_alerts.append({
                    "time": offset_str,
                    "severity": "MEDIUM",
                    "classification": "Unauthorized Entry",
                    "details": f"Intrusion detected: Person ID {pid} entered secure area."
                })
            elif ev["event_type"] == "loitering_detection":
                duration = int(ev["details"].get("duration_seconds", 20))
                formatted_events.append({
                    "time": offset_str,
                    "type": "ALERT_TRIGGERED",
                    "id": pid,
                    "log": f"ALERT [HIGH]: Suspicious loitering detected: Person ID {pid} observed in secure area for {duration}s."
                })
                formatted_alerts.append({
                    "time": offset_str,
                    "severity": "HIGH",
                    "classification": "Suspicious Loitering",
                    "details": f"Suspicious loitering detected: Person ID {pid} observed in secure area for {duration}s."
                })

        report_keyframes = []
        for kf in self.run_keyframes:
            offset_sec = (kf["timestamp"] - self.run_start_time).total_seconds()
            offset_str = format_offset(offset_sec)
            report_keyframes.append({
                "url": kf["url"],
                "offset": offset_str,
                "index": kf["index"]
            })

        report_data = {
            "uuid": self.run_uuid,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_footage": os.path.basename(self.stream_source),
            "metrics": {
                "total_persons": len(self.tracked_persons),
                "total_bags": len(self.tracked_bags),
                "total_vehicles": len(self.tracked_vehicles),
                "alerts_count": len(formatted_alerts),
                "events_count": len(formatted_events)
            },
            "alerts": formatted_alerts,
            "events": formatted_events,
            "keyframes": report_keyframes
        }
        
        report_path = os.path.join(report_dir, f"report_{self.run_uuid}.json")
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=4)
            
        logger.info(f"Forensic report generated: {report_path}")

# Global pipeline instance
video_pipeline = VideoPipelineManager()
