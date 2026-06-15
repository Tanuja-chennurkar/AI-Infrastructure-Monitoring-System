from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from app.events.base_rule import BaseRule
from app.events.rules.suspicious_bag import SuspiciousBagRule
from app.events.rules.loitering import LoiteringRule
from app.core.logging import logger

class EventEngine:
    """Orchestrates the evaluation of registered security rules on incoming video frames."""
    
    def __init__(self) -> None:
        self.rules: List[BaseRule] = [
            SuspiciousBagRule(),
            LoiteringRule()
        ]
        logger.info(f"EventEngine initialized with {len(self.rules)} rules: {[r.rule_name for r in self.rules]}")

    def evaluate(
        self,
        detections: List[Dict[str, Any]],
        tracked_objects: List[Dict[str, Any]],
        stream_id: str,
        timestamp: datetime
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """
        Runs all registered rules on the current frame.
        
        Returns a list of (event_data, optional_alert_data) tuples.
        """
        all_results = []
        
        for rule in self.rules:
            try:
                rule_results = rule.evaluate(detections, tracked_objects, stream_id, timestamp)
                if rule_results:
                    all_results.extend(rule_results)
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule.rule_name}': {e}")
                
        return all_results
