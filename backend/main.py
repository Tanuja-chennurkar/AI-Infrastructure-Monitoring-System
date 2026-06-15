from fastapi import FastAPI
from routes.metrics import router as metrics_router
from routes.anomaly import router as anomaly_router
from routes.insights import router as insights_router
from routes.alerts import router as alerts_router

app = FastAPI(
    title="Monitoring Analytics API",
    version="1.0.0"
)

app.include_router(metrics_router)
app.include_router(anomaly_router)
app.include_router(insights_router)
app.include_router(alerts_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Monitoring API"
    }