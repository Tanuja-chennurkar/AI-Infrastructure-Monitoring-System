from fastapi import APIRouter
from prometheus_service import query_prometheus

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"]
)

@router.get("/cpu")
def get_cpu():

    query = "sum(rate(container_cpu_usage_seconds_total[1m]))"

    data = query_prometheus(query)

    print(data)

    result = data["data"]["result"]

    if not result:
        return {"cpu_usage": 0}

    cpu_usage = float(result[0]["value"][1])

    return {
        "raw_cpu_usage": cpu_usage
    }
    
@router.get("/memory")
def get_memory():

    query = "sum(container_memory_usage_bytes)"

    data = query_prometheus(query)

    result = data["data"]["result"]

    if not result:
        return {"memory_usage_mb": 0}

    memory_bytes = float(result[0]["value"][1])

    return {
        "memory_usage_mb": round(memory_bytes / (1024 * 1024), 2)
    }
    
@router.get("/network")
def get_network():

    query = "sum(rate(container_network_receive_bytes_total[1m]))"

    data = query_prometheus(query)

    result = data["data"]["result"]

    if not result:
        return {"network_receive_bytes_per_sec": 0}

    network = float(result[0]["value"][1])

    return {
        "network_receive_bytes_per_sec": round(network, 2)
    }