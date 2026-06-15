import unittest
from datetime import datetime, timedelta
from app.events.rules.suspicious_bag import SuspiciousBagRule
from app.events.rules.loitering import LoiteringRule

class TestEventRules(unittest.TestCase):
    
    def setUp(self) -> None:
        self.stream_id = "test_stream"
        self.now = datetime.utcnow()

    def test_suspicious_bag_rule_trigger(self) -> None:
        rule = SuspiciousBagRule()
        
        # Test Case 1: Only person present -> No alert
        detections = [{"class_name": "person", "box": [0,0,10,10], "confidence": 0.9}]
        tracks = [{"track_id": "1", "box": [0,0,10,10], "class_name": "person"}]
        results = rule.evaluate(detections, tracks, self.stream_id, self.now)
        self.assertEqual(len(results), 0)

        # Test Case 2: Person + Bag present simultaneously -> Alert triggered
        detections.append({"class_name": "backpack", "box": [12,12,20,20], "confidence": 0.8})
        tracks.append({"track_id": "2", "box": [12,12,20,20], "class_name": "backpack"})
        results = rule.evaluate(detections, tracks, self.stream_id, self.now)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0]["event_type"], "suspicious_object_presence")
        self.assertEqual(results[0][0]["tracking_id"], "1")
        self.assertEqual(results[0][1]["alert_type"], "Suspicious Object")

        # Test Case 3: Re-evaluate same frame (spam prevention check) -> No new alerts
        results_again = rule.evaluate(detections, tracks, self.stream_id, self.now)
        self.assertEqual(len(results_again), 0)

    def test_loitering_rule_trigger(self) -> None:
        rule = LoiteringRule(loitering_threshold_seconds=20.0)
        
        # Test Case 1: First view of track ID 1 -> No alert
        tracks = [{"track_id": "1", "box": [0,0,10,10], "class_name": "person"}]
        results = rule.evaluate([], tracks, self.stream_id, self.now)
        self.assertEqual(len(results), 0)

        # Test Case 2: Track ID 1 visible for 10s (under threshold) -> No alert
        t_10s = self.now + timedelta(seconds=10)
        results = rule.evaluate([], tracks, self.stream_id, t_10s)
        self.assertEqual(len(results), 0)

        # Test Case 3: Track ID 1 visible for 21s (exceeds threshold) -> Alert triggered
        t_21s = self.now + timedelta(seconds=21)
        results = rule.evaluate([], tracks, self.stream_id, t_21s)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0]["event_type"], "loitering_detection")
        self.assertEqual(results[0][0]["tracking_id"], "1")
        self.assertEqual(results[0][1]["alert_type"], "Loitering")

        # Test Case 4: Subsequent frames -> No duplicate alert
        t_22s = self.now + timedelta(seconds=22)
        results = rule.evaluate([], tracks, self.stream_id, t_22s)
        self.assertEqual(len(results), 0)

        # Test Case 5: Track ID disappears and exceeds grace period -> Resets tracking
        t_30s = self.now + timedelta(seconds=30)
        # Empty tracks simulating disappearance
        rule.evaluate([], [], self.stream_id, t_30s)
        
        # If ID returns later, starts fresh
        t_35s = self.now + timedelta(seconds=35)
        results = rule.evaluate([], tracks, self.stream_id, t_35s)
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
