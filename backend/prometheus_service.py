import requests
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9090"


def query_prometheus(query: str):
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def query_prometheus_range(
    query: str,
    minutes: int = 60,
    step: str = "30s"
):
    end = datetime.now()
    start = end - timedelta(minutes=minutes)

    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step
        },
        timeout=10
    )

    print("URL:", response.url)

    response.raise_for_status()
    return response.json()