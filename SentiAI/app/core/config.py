import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Base directory of the project
    BASE_DIR: Path = BASE_DIR

    # App Settings
    APP_NAME: str = "SentinelAI"
    DEBUG: bool = False
    
    # Video Ingestion
    # Can be: "0" (webcam), "/path/to/video.mp4", or "mock" (for generated frames if no device available)
    VIDEO_SOURCE: str = "mock"
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    FPS: int = 30
    
    # YOLO Settings
    YOLO_MODEL: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.45
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./sentinel.db"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure critical directories exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "videos"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "keyframes"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "reports"), exist_ok=True)
