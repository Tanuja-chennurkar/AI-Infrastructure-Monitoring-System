from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
from app.events.base_rule import BaseRule
from app.core.logging import logger

class LoiteringRule(BaseRule):
    """
    Rule 2: Loitering Detection
    Condition: Same tracked person remains visible for more than 20 seconds.
    Output: Alert: "Loitering detected"
    """
    
    def __init__(self, loitering_threshold_seconds: float = 20.0) -> None:
        self.loitering_threshold = loitering_threshold_seconds
        
        # Track ID -> First seen datetime
        self._first_seen: Dict[str, datetime] = {}
        # Track ID -> Last seen datetime (to handle short gaps/occlusions)
        self._last_seen: Dict[str, datetime] = {}
        # Track IDs that have already triggered a loitering alert in their current session
        self._alerted_ids: Set[str] = set()
        
        # Grace period in seconds to keep track of a person who temporarily disappears
        self._occlusion_grace_seconds: float = 5.0

    @property
    def rule_name(self) -> str:
        return "loitering"

    def evaluate(
        self,
        detections: List[Dict[str, Any]],
        tracked_objects: List[Dict[str, Any]],
        stream_id: str,
        timestamp: datetime
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        
        # Identify active person tracking IDs in the current frame
        active_person_tracks = [obj for obj in tracked_objects if obj["class_name"] == "person"]
        active_person_ids = {p["track_id"] for p in active_person_tracks}
        
        results = []
        
        # 1. Update tracking timestamps for visible people
        for person in active_person_tracks:
            pid = person["track_id"]
            self._last_seen[pid] = timestamp
            
            # If we haven't seen this track before, record the start time
            if pid not in self._first_seen:
                self._first_seen[pid] = timestamp
                logger.debug(f"[LOITERING] Tracked person {pid} first seen at {timestamp}")
            
            # Calculate duration visible
            duration = (timestamp - self._first_seen[pid]).total_seconds()
            
            # If duration exceeds loitering threshold and we haven't alerted yet
            if duration >= self.loitering_threshold and pid not in self._alerted_ids:
                self._alerted_ids.add(pid)
                
                event_data = {
                    "event_type": "loitering_detection",
                    "tracking_id": pid,
                    "source_stream": stream_id,
                    "details": {
                        "duration_seconds": round(duration, 2),
                        "message": f"Person ID {pid} observed in stream for {round(duration, 1)} seconds.",
                        "box": person["box"]
                    }
                }
                
                alert_data = {
                    "alert_type": "Loitering",
                    "message": f"Loitering detected (Person ID: {pid}, Duration: {int(duration)}s)",
                    "status": "active"
                }
                
                logger.info(f"[RULE] Loitering rule triggered for Person ID: {pid} (Duration: {round(duration, 1)}s)")
                results.append((event_data, alert_data))
                
        # 2. Clean up expired tracks (people who left the frame and did not return within grace period)
        expired_pids = []
        for pid, last_seen_time in self._last_seen.items():
            if pid not in active_person_ids:
                # If they've been gone longer than the occlusion grace period, expire them
                elapsed_since_seen = (timestamp - last_seen_time).total_seconds()
                if elapsed_since_seen > self._occlusion_grace_seconds:
                    expired_pids.append(pid)
                    
        for pid in expired_pids:
            logger.debug(f"[LOITERING] Cleaning up expired track {pid} (inactive for > {self._occlusion_grace_seconds}s)")
            self._first_seen.pop(pid, None)
            self._last_seen.pop(pid, None)
            self._alerted_ids.discard(pid)

        return results
