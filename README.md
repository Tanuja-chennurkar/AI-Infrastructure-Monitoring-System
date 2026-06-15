
# AI Infrastructure Monitoring System

## Overview

AI Infrastructure Monitoring System is a full-stack observability platform designed to monitor, analyze, and visualize the runtime behavior of AI workloads deployed in Docker containers.

The project integrates a real-world AI video analytics application (SentinelAI) with industry-standard monitoring tools including Prometheus, Grafana, and cAdvisor. It continuously collects infrastructure metrics, performs anomaly detection, generates alerts, and provides actionable insights through a centralized dashboard.

---

## Key Features

### Real-Time Monitoring

* Container CPU monitoring
* Container memory monitoring
* Container network monitoring
* Docker container observability using cAdvisor

### Metrics Collection

* Prometheus-based metrics scraping
* Time-series metric storage
* Historical metric analysis

### Anomaly Detection Engine

* Z-Score based anomaly detection
* Percentile based anomaly detection
* Rolling window anomaly detection
* Severity classification

### Alert Management

* Automatic anomaly alerts
* Severity-based alert categorization
* Alert history management
* Alert clearing functionality

### System Insights

* Infrastructure health score
* Resource utilization analysis
* Automated recommendations
* Health status reporting

### Visualization

* Grafana dashboards
* Real-time metric visualization
* Performance trend analysis
* Monitoring panels for AI workloads

---

## System Architecture

```text
+---------------------+
|     SentinelAI      |
|  AI Video Analytics |
+----------+----------+
           |
           v
+---------------------+
|      Docker         |
|    Containers       |
+----------+----------+
           |
           v
+---------------------+
|      cAdvisor       |
| Container Metrics   |
+----------+----------+
           |
           v
+---------------------+
|     Prometheus      |
| Time Series DB      |
+----------+----------+
           |
           v
+---------------------+
|  FastAPI Analytics  |
| Anomaly Detection   |
| Alerts & Insights   |
+----------+----------+
           |
           v
+---------------------+
|      Grafana        |
| Visualization Layer |
+---------------------+
```

---

## Technology Stack

### Backend

* Python
* FastAPI

### Monitoring

* Prometheus
* Grafana
* cAdvisor

### AI Application

* YOLOv8
* DeepSORT
* OpenCV

### Containerization

* Docker
* Docker Compose

### Data Analysis

* NumPy
* SciPy

---

## Project Structure

```text
MonitoringDashboard
│
├── backend
│   ├── routes
│   ├── services
│   ├── main.py
│   └── prometheus_service.py
│
├── prometheus
│   └── prometheus.yml
│
├── SentiAI
│   ├── app
│   ├── data
│   ├── logs
│   ├── videos
│   ├── Dockerfile
│   └── requirements.txt
│
└── docker-compose.yml
```

---

## API Endpoints

### Anomaly Detection

#### CPU Analysis

```http
GET /anomaly/cpu
```

Response:

```json
{
  "severity": "normal",
  "z_score": -0.47,
  "statistics": {},
  "anomaly_score": 0
}
```

---

#### Memory Analysis

```http
GET /anomaly/memory
```

---

#### Network Analysis

```http
GET /anomaly/network
```

---

### Alerts

#### Get Alerts

```http
GET /alerts
```

---

#### Clear Alerts

```http
DELETE /alerts
```

---

### Insights

#### System Health

```http
GET /insights
```

Example Response:

```json
{
  "system_health": "healthy",
  "health_score": 100,
  "cpu_status": "normal",
  "memory_status": "normal",
  "network_status": "normal"
}
```

---

## Grafana Dashboard

The dashboard visualizes:

* SentinelAI CPU utilization
* SentinelAI memory utilization
* SentinelAI network traffic
* Infrastructure trends
* Resource consumption patterns

### Example Metrics

CPU

```promql
rate(container_cpu_usage_seconds_total{name="sentinel_ai_container"}[1m])
```

Memory

```promql
container_memory_usage_bytes{name="sentinel_ai_container"}
```

Network

```promql
rate(container_network_receive_bytes_total{name="sentinel_ai_container"}[1m])
```

---

## Running the Project

### Clone Repository

```bash
git clone https://github.com/<username>/AI-Infrastructure-Monitoring-System.git
cd AI-Infrastructure-Monitoring-System
```

### Start Services

```bash
docker compose up --build -d
```

---

## Service URLs

### Monitoring Analytics API

```text
http://localhost:8000
```

### Grafana

```text
http://localhost:3000
```

### Prometheus

```text
http://localhost:9090
```

### cAdvisor

```text
http://localhost:8081
```

### SentinelAI

```text
http://localhost:8001
```

---

## Validation Performed

The platform was validated through:

* SentinelAI container monitoring
* CPU metric collection
* Memory metric collection
* Network metric collection
* Real-time anomaly detection
* Alert generation
* Health insight generation
* Grafana dashboard visualization
* End-to-end monitoring workflow verification

---

## Future Improvements

* Machine Learning based anomaly detection
* Alert notifications via Email and Slack
* Kubernetes monitoring support
* Multi-container AI workload monitoring
* Predictive infrastructure analytics
* Distributed tracing integration

---

## Resume Highlights

* Built an AI infrastructure monitoring platform using Prometheus, Grafana, FastAPI, Docker, and cAdvisor.
* Developed statistical anomaly detection using Z-Score, percentile analysis, and rolling-window techniques.
* Integrated monitoring with a YOLOv8-based AI surveillance system to provide real-time infrastructure observability.
* Designed automated alerting and system health scoring mechanisms for containerized AI workloads.

---

## Author

Tanuja Chennurkar

AI Infrastructure Monitoring System
2026
