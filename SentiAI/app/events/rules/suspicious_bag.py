from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
from app.events.base_rule import BaseRule
from app.core.logging import logger

class SuspiciousBagRule(BaseRule):
    """
    Rule 1: Suspicious Object Presence
    Condition: Person and bag (backpack, handbag, suitcase) detected simultaneously.
    Output: Alert: "Person carrying bag detected"
    """
    
    def __init__(self) -> None:
        # Cache of tracked person IDs for which we have already raised this alert
        self._alerted_person_ids: Set[str] = set()
        # Cooldown for untracked detections to prevent spam
        self._last_untracked_alert_time: Optional[datetime] = None
        self._untracked_cooldown_seconds: float = 10.0

    @property
    def rule_name(self) -> str:
        return "suspicious_bag"

    def evaluate(
        self,
        detections: List[Dict[str, Any]],
        tracked_objects: List[Dict[str, Any]],
        stream_id: str,
        timestamp: datetime
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        
        # Determine if person and bag are present in current frame
        has_person = False
        has_bag = False
        bag_types = {"backpack", "handbag", "suitcase"}
        
        # Check from current tracked objects
        tracked_people = [obj for obj in tracked_objects if obj["class_name"] == "person"]
        tracked_bags = [obj for obj in tracked_objects if obj["class_name"] in bag_types]
        
        # Fallback to raw detections if tracking is still initializing
        raw_people = [det for det in detections if det["class_name"] == "person"]
        raw_bags = [det for det in detections if det["class_name"] in bag_types]
        
        has_person = len(tracked_people) > 0 or len(raw_people) > 0
        has_bag = len(tracked_bags) > 0 or len(raw_bags) > 0
        
        if not (has_person and has_bag):
            return []

        results = []
        
        # 1. Handle tracked people to raise targeted alerts
        for person in tracked_people:
            pid = person["track_id"]
            if pid not in self._alerted_person_ids:
                self._alerted_person_ids.add(pid)
                
                event_data = {
                    "event_type": "suspicious_object_presence",
                    "tracking_id": pid,
                    "source_stream": stream_id,
                    "details": {
                        "message": f"Tracked person ID {pid} and bag detected in frame.",
                        "person_box": person["box"]
                    }
                }
                
                alert_data = {
                    "alert_type": "Suspicious Object",
                    "message": f"Person carrying bag detected (Person ID: {pid})",
                    "status": "active"
                }
                
                logger.info(f"[RULE] Suspicious bag rule triggered for Person ID: {pid}")
                results.append((event_data, alert_data))
                
        # 2. Fallback: If person and bag are detected but person is not yet tracked (no track_id)
        if not results and len(raw_people) > 0:
            # Check cooldown to prevent flooding
            should_alert = False
            if self._last_untracked_alert_time is None:
                should_alert = True
            else:
                elapsed = (timestamp - self._last_untracked_alert_time).total_seconds()
                if elapsed >= self._untracked_cooldown_seconds:
                    should_alert = True
                    
            if should_alert:
                self._last_untracked_alert_time = timestamp
                event_data = {
                    "event_type": "suspicious_object_presence",
                    "tracking_id": None,
                    "source_stream": stream_id,
                    "details": {"message": "Untracked person and bag detected simultaneously."}
                }
                
                alert_data = {
                    "alert_type": "Suspicious Object",
                    "message": "Person carrying bag detected",
                    "status": "active"
                }
                
                logger.info("[RULE] Suspicious bag rule triggered for untracked targets")
                results.append((event_data, alert_data))
                
        # Clean up alerted person IDs if they are no longer in active tracking list to prevent memory bloat
        # We only clean up if the set is getting large and the IDs are no longer tracked
        if len(self._alerted_person_ids) > 100:
            active_ids = {obj["track_id"] for obj in tracked_objects}
            self._alerted_person_ids = {pid for pid in self._alerted_person_ids if pid in active_ids}

        return results
