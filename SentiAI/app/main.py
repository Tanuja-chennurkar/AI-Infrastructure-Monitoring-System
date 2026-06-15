import os
import json
import glob
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.api.endpoints import router as api_router
from app.database.session import engine, Base, get_db
from app.database.models import EventModel, AlertModel
from app.services.video_service import video_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up SentinelAI backend service...")
    try:
        # Create database tables if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise e
        
    yield
    
    # Shutdown actions
    logger.info("Shutting down SentinelAI backend service...")
    if video_pipeline.is_active:
        video_pipeline.stop()
    logger.info("Backend service shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    description="SentinelAI Multi-Source Video Analysis and Interpretation System Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware (useful for future frontend integrations)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")

# Mount Static Files (for serving uploaded videos and saved keyframes/reports)
app.mount("/static", StaticFiles(directory=os.path.join(settings.BASE_DIR, "static")), name="static")

# Set up templates path
TEMPLATE_DIR = os.path.join(settings.BASE_DIR, "app", "dashboard", "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@app.get("/", response_class=HTMLResponse, summary="Serve SentinelAI Analytics Dashboard")
def serve_dashboard(request: Request, db: Session = Depends(get_db)):
    """Renders and serves the HTML administration dashboard."""
    events = db.query(EventModel).order_by(EventModel.timestamp.desc()).limit(15).all()
    alerts = db.query(AlertModel).order_by(AlertModel.timestamp.desc()).limit(15).all()
    status = video_pipeline.get_status()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "events": events,
            "alerts": alerts,
            "status": status,
            "config": {
                "source": settings.VIDEO_SOURCE,
                "confidence": settings.CONFIDENCE_THRESHOLD,
                "model": settings.YOLO_MODEL
            }
        }
    )

@app.get("/report", response_class=HTMLResponse, summary="Serve Forensic Investigation Report")
def serve_report(request: Request, uuid: str = None):
    """Renders the forensic report for a specific run UUID or the latest run."""
    report_dir = os.path.join(settings.BASE_DIR, "static", "reports")
    report_data = None
    
    # Get all reports history to let the user navigate
    all_reports = []
    if os.path.exists(report_dir):
        files = glob.glob(os.path.join(report_dir, "report_*.json"))
        # Sort by file modification time descending
        files.sort(key=os.path.getmtime, reverse=True)
        for f_path in files:
            try:
                with open(f_path, "r") as f:
                    data = json.load(f)
                    all_reports.append({
                        "uuid": data["uuid"],
                        "source_footage": data["source_footage"],
                        "generated_at": data["generated_at"]
                    })
            except Exception:
                pass

    if uuid:
        report_path = os.path.join(report_dir, f"report_{uuid}.json")
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_data = json.load(f)
    else:
        # Load the latest report
        if os.path.exists(report_dir):
            files = glob.glob(os.path.join(report_dir, "report_*.json"))
            if files:
                latest_file = max(files, key=os.path.getmtime)
                try:
                    with open(latest_file, "r") as f:
                        report_data = json.load(f)
                except Exception:
                    pass

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "report": report_data,
            "history": all_reports,
            "selected_uuid": uuid or (report_data["uuid"] if report_data else None)
        }
    )
