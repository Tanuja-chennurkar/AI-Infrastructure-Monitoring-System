import os
import json
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import shutil
import uuid
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import numpy as np
import cv2

from app.database.session import get_db
from app.database.models import EventModel, AlertModel
from app.services.video_service import video_pipeline
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import (
    HealthResponse,
    StreamStatusResponse,
    StartStreamRequest,
    StartStreamResponse,
    StopStreamResponse,
    EventResponse,
    AlertResponse
)

router = APIRouter()

def get_offline_frame() -> bytes:
    """Generates a high-quality 'STREAM OFFLINE' placeholder frame."""
    img = np.zeros((settings.FRAME_HEIGHT, settings.FRAME_WIDTH, 3), dtype=np.uint8)
    
    # Draw simple dark tech design grid
    for x in range(0, settings.FRAME_WIDTH, 40):
        cv2.line(img, (x, 0), (x, settings.FRAME_HEIGHT), (15, 15, 20), 1)
    for y in range(0, settings.FRAME_HEIGHT, 40):
        cv2.line(img, (0, y), (settings.FRAME_WIDTH, y), (15, 15, 20), 1)
        
    cv2.putText(img, "STREAM OFFLINE", (170, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (75, 75, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "Use dashboard to start the camera feed", (140, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1, cv2.LINE_AA)
    _, jpeg = cv2.imencode('.jpg', img)
    return jpeg.tobytes()

async def mjpeg_frame_generator():
    """Generates MJPEG multipart frames for the live dashboard feed."""
    logger.info("MJPEG stream connection opened.")
    try:
        while True:
            if video_pipeline.is_active:
                frame_bytes = video_pipeline.get_current_frame_jpeg()
                if frame_bytes is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    await asyncio.sleep(0.01)
            else:
                frame_bytes = get_offline_frame()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(1.0)  # Lower refresh rate when offline
                
            await asyncio.sleep(0.033)  # Yield control, run at roughly 30 FPS
    except asyncio.CancelledError:
        logger.info("MJPEG stream connection closed by client.")
    except Exception as e:
        logger.error(f"Error in MJPEG frame generator: {e}")

@router.get("/health", response_model=HealthResponse, summary="Perform System Health Check")
def health_check():
    """Simple health check endpoint returning system status."""
    return HealthResponse(status="healthy")

@router.get("/stream-status", response_model=StreamStatusResponse, summary="Get Video Ingestion Pipeline Status")
def get_stream_status():
    """Returns the current state and metrics of the ingestion pipeline."""
    return video_pipeline.get_status()

@router.post("/start-stream", response_model=StartStreamResponse, summary="Activate Video Ingestion Stream")
def start_stream(payload: StartStreamRequest):
    """Starts the background video pipeline processing thread with the specified source."""
    # Ensure source path exists if it is an MP4 path and not webcam/mock
    src = payload.source
    if src not in ["mock", "0"] and not src.isdigit():
        # Clean relative paths or confirm existence
        if not os.path.exists(src):
            # Try searching under settings.BASE_DIR / videos or static/videos
            alternative_path = os.path.join(settings.BASE_DIR, "videos", src)
            static_path = os.path.join(settings.BASE_DIR, "static", "videos", src)
            if os.path.exists(alternative_path):
                src = alternative_path
            elif os.path.exists(static_path):
                src = static_path
            else:
                logger.warning(f"Video file source path {payload.source} not found. Defaulting to mock.")
                src = "mock"

    success = video_pipeline.start(source=src)
    if not success:
        raise HTTPException(status_code=400, detail="Stream is already active or failed to initialize.")
        
    return StartStreamResponse(
        success=True,
        message=f"Pipeline initialized with source: {src}",
        status=video_pipeline.get_status()
    )

@router.post("/stop-stream", response_model=StopStreamResponse, summary="Deactivate Video Ingestion Stream")
def stop_stream():
    """Stops the background video pipeline processing thread."""
    success = video_pipeline.stop()
    if not success:
        raise HTTPException(status_code=400, detail="Stream is not active.")
    return StopStreamResponse(success=True, message="Pipeline stopped successfully.")

@router.get("/stream/video_feed", summary="Live MJPEG Video Feed")
def get_video_feed():
    """Stream live annotated frames as MJPEG multipart response."""
    return StreamingResponse(
        mjpeg_frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/events", response_model=List[EventResponse], summary="Retrieve Logged Security Events")
def get_events(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fetches list of the most recent security events detected in the system."""
    events = db.query(EventModel).order_by(EventModel.timestamp.desc()).limit(limit).all()
    
    # Parse json string details to Dict
    parsed_events = []
    for ev in events:
        details_dict = {}
        if ev.details:
            try:
                details_dict = json.loads(ev.details)
            except Exception:
                details_dict = {"raw_value": ev.details}
                
        parsed_events.append(EventResponse(
            id=ev.id,
            timestamp=ev.timestamp,
            event_type=ev.event_type,
            tracking_id=ev.tracking_id,
            source_stream=ev.source_stream,
            details=details_dict
        ))
        
    return parsed_events

@router.get("/alerts", response_model=List[AlertResponse], summary="Retrieve Critical Alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fetches list of the most recent active/resolved alerts."""
    return db.query(AlertModel).order_by(AlertModel.timestamp.desc()).limit(limit).all()

@router.post("/upload-video", summary="Upload a video file for forensic analysis")
def upload_video(file: UploadFile = File(...)):
    """Saves an uploaded video file to the static/videos directory."""
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format. Supported formats: mp4, avi, mov, mkv.")
        
    static_video_dir = os.path.join(settings.BASE_DIR, "static", "videos")
    os.makedirs(static_video_dir, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(static_video_dir, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
        
    return {
        "success": True, 
        "filename": unique_filename,
        "original_name": file.filename,
        "url": f"/static/videos/{unique_filename}"
    }
