import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.services.video_service import video_pipeline

class TestApiEndpoints(unittest.TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Ensure stream is stopped before running each test
        if video_pipeline.is_active:
            video_pipeline.stop()

    def tearDown(self) -> None:
        # Ensure stream is stopped after running each test
        if video_pipeline.is_active:
            video_pipeline.stop()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    def test_stream_status_endpoint(self) -> None:
        response = self.client.get("/api/stream-status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_running"])
        self.assertEqual(data["source"], "mock")

    def test_start_stop_stream_pipeline(self) -> None:
        # Test starting mock stream
        response = self.client.post("/api/start-stream", json={"source": "mock"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["status"]["is_running"])
        self.assertEqual(data["status"]["source"], "mock")
        
        # Test double starting -> Should fail or return 400 as per endpoints.py design
        response_dup = self.client.post("/api/start-stream", json={"source": "mock"})
        self.assertEqual(response_dup.status_code, 400)

        # Test status endpoint while running
        response_status = self.client.get("/api/stream-status")
        self.assertEqual(response_status.status_code, 200)
        self.assertTrue(response_status.json()["is_running"])

        # Test stopping stream
        response_stop = self.client.post("/api/stop-stream")
        self.assertEqual(response_stop.status_code, 200)
        self.assertTrue(response_stop.json()["success"])

        # Check status again
        response_status_final = self.client.get("/api/stream-status")
        self.assertEqual(response_status_final.status_code, 200)
        self.assertFalse(response_status_final.json()["is_running"])

    def test_get_events_endpoint(self) -> None:
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_alerts_endpoint(self) -> None:
        response = self.client.get("/api/alerts")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == '__main__':
    unittest.main()
