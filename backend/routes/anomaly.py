from fastapi import APIRouter

from prometheus_service import query_prometheus_range
from services.anomaly_service import AnomalyService
from services.alert_service import AlertService

router = APIRouter(
    prefix="/anomaly",
    tags=["Anomaly Detection"]
)


def analyze_metric(query, metric_name):

    data = query_prometheus_range(
        query=query,
        minutes=5,
        step="15s"
    )

    result = data["data"]["result"]

    if not result:
        return {"error": "No data available"}

    values = [
        float(point[1])
        for point in result[0]["values"]
    ]

    stats = AnomalyService.calculate_statistics(values)

    z_score = AnomalyService.z_score(values)

    percentile_flag = (
        AnomalyService.percentile_anomaly(values)
    )

    rolling_flag = (
        AnomalyService.rolling_window_anomaly(values)
    )

    anomaly_score = 0

    if abs(z_score) > 3:
        anomaly_score += 1

    if percentile_flag:
        anomaly_score += 1

    if rolling_flag:
        anomaly_score += 1

    severity_map = {
        0: "normal",
        1: "low",
        2: "medium",
        3: "high"
    }

    severity = severity_map.get(
        min(anomaly_score, 3),
        "high"
    )

    if anomaly_score > 0:

        AlertService.add_alert(
            metric=metric_name,
            severity=severity,
            message=f"{metric_name.upper()} anomaly detected"
        )

    return {
        "severity": severity,
        "z_score": round(z_score, 3),
        "statistics": stats,
        "anomaly_score": anomaly_score
    }


@router.get("/cpu")
def cpu_anomaly():

     return analyze_metric(
        'rate(container_cpu_usage_seconds_total{name="sentinel_ai_container"}[1m])',
        "cpu"
    )


@router.get("/memory")
def memory_anomaly():

    return analyze_metric(
        'container_memory_usage_bytes{name="sentinel_ai_container"}',
        "memory"
    )


@router.get("/network")
def network_anomaly():

    return analyze_metric(
        'rate(container_network_receive_bytes_total{name="sentinel_ai_container"}[1m])',
        "network"
    )
    