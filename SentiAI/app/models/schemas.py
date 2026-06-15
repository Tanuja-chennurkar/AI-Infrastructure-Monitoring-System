from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime = Field(..., default_factory=datetime.utcnow)

class StreamStatusResponse(BaseModel):
    is_running: bool = Field(..., example=True)
    source: str = Field(..., example="mock")
    fps: float = Field(..., example=29.9)
    processed_frames: int = Field(..., example=150)
    uptime_seconds: int = Field(..., example=5)
    run_uuid: Optional[str] = Field(None, example="ad30aa30-fedc-431b-afa9-e24dddf8ea6f")

class StartStreamRequest(BaseModel):
    source: str = Field(default="mock", description="Stream source (e.g. 'mock', '0', 'videos/test.mp4')")

class StartStreamResponse(BaseModel):
    success: bool = Field(..., example=True)
    message: str = Field(..., example="Stream started successfully.")
    status: StreamStatusResponse

class StopStreamResponse(BaseModel):
    success: bool = Field(..., example=True)
    message: str = Field(..., example="Stream stopped successfully.")

class EventResponse(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    tracking_id: Optional[str] = None
    source_stream: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    timestamp: datetime
    alert_type: str
    message: str
    event_id: Optional[int] = None
    status: str

    class Config:
        from_attributes = True
