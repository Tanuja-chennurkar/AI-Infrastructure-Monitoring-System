from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

class BaseRule(ABC):
    """Abstract base class that all security detection rules must implement."""
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Returns the unique name of this rule."""
        pass

    @abstractmethod
    def evaluate(
        self,
        detections: List[Dict[str, Any]],
        tracked_objects: List[Dict[str, Any]],
        stream_id: str,
        timestamp: datetime
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """
        Evaluates the rule against detections and tracked objects for a frame.
        
        Returns a list of tuples: (event_data, optional_alert_data)
        where:
        - event_data: dict containing keys:
            - "event_type": str
            - "tracking_id": Optional[str]
            - "source_stream": str
            - "details": Dict[str, Any]
        - alert_data: dict containing keys (or None if no alert triggered):
            - "alert_type": str
            - "message": str
            - "status": str
        """
        pass
