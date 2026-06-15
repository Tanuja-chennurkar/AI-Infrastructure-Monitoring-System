from fastapi import APIRouter

from services.alert_service import AlertService

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/")
def get_alerts():

    return {
        "count": len(AlertService.get_alerts()),
        "alerts": AlertService.get_alerts()
    }


@router.delete("/")
def clear_alerts():

    AlertService.clear_alerts()

    return {
        "message": "All alerts cleared"
    }