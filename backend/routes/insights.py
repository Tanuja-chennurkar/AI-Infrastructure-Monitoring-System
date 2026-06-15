from fastapi import APIRouter

from routes.anomaly import (
    cpu_anomaly,
    memory_anomaly,
    network_anomaly
)

router = APIRouter(
    prefix="/insights",
    tags=["AI Insights"]
)


@router.get("/")
def get_insights():

    cpu = cpu_anomaly()
    memory = memory_anomaly()
    network = network_anomaly()

    cpu_score = cpu["anomaly_score"]
    memory_score = memory["anomaly_score"]
    network_score = network["anomaly_score"]

    health_score = 100

    health_score -= cpu_score * 10
    health_score -= memory_score * 10
    health_score -= network_score * 10

    health_score = max(0, health_score)

    recommendations = []

    if cpu_score > 0:
        recommendations.append(
            "Investigate CPU-intensive workloads."
        )

    if memory_score > 0:
        recommendations.append(
            "Check for memory pressure or leaks."
        )

    if network_score > 0:
        recommendations.append(
            "Inspect network traffic patterns."
        )

    if health_score >= 90:
        system_health = "healthy"

    elif health_score >= 70:
        system_health = "warning"

    else:
        system_health = "critical"

    summary = (
        "All monitored resources are operating within expected limits."
        if not recommendations
        else "Resource anomalies detected."
    )

    return {
        "system_health": system_health,
        "health_score": health_score,

        "cpu_status": cpu["severity"],
        "memory_status": memory["severity"],
        "network_status": network["severity"],

        "summary": summary,
        "recommendations": recommendations
    }