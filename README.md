# AI Infrastructure Monitoring System with SentinelAI

## Overview

AI Infrastructure Monitoring System is a production-inspired MLOps and Observability platform built around **SentinelAI**, an intelligent video surveillance analytics application. The project combines real-time AI inference with modern observability practices to demonstrate how machine learning workloads can be monitored, analyzed, and maintained in a containerized environment.

Unlike traditional monitoring projects that focus only on infrastructure metrics, this platform provides end-to-end visibility into both the AI application and the underlying system. It integrates metrics, logs, traces, and anomaly detection into a unified observability ecosystem powered by Grafana.

The project is divided into two tightly integrated components:

### SentinelAI – Intelligent Surveillance Analytics

SentinelAI is a computer vision application that analyzes video streams and identifies potentially suspicious activities in real time. The system processes incoming frames using AI models, applies event detection rules, and generates alerts and forensic reports for security analysis.

Key capabilities include:

* Real-time object detection using YOLO
* Suspicious bag detection
* Loitering detection
* Event correlation and alert generation
* Investigation report generation
* Historical event tracking
* Dashboard-driven incident analysis
* RESTful API built with FastAPI

### Monitoring & Observability Platform

The monitoring platform provides complete visibility into the AI application's behavior and infrastructure performance. It follows modern observability principles by collecting and correlating metrics, logs, and distributed traces.

Key capabilities include:

* Real-time infrastructure monitoring
* Container resource tracking
* Centralized log aggregation
* Distributed request tracing
* Application performance analysis
* ML-based anomaly detection
* Unified Grafana dashboards
* End-to-end observability workflows

---

## System Architecture

```text
                    ┌────────────────────────┐
                    │      Video Sources     │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │       SentinelAI       │
                    │   AI Inference Layer   │
                    └────────────┬───────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼

      Prometheus          Loki Logs         Tempo Traces
        Metrics                             OpenTelemetry

              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼

                         Grafana Dashboard
                    Unified Observability Layer
```

---

## Core Features

### AI & Video Analytics

* AI-powered surveillance monitoring
* Real-time object detection
* Event-driven alert generation
* Suspicious activity detection
* Forensic investigation reports
* Historical event analysis

### Infrastructure Monitoring

* CPU utilization monitoring
* Memory utilization monitoring
* Network traffic monitoring
* Docker container monitoring
* Resource consumption analytics

### Centralized Logging

* Log aggregation using Loki
* Container log collection using Promtail
* Real-time log streaming
* Error and warning log analysis

### Distributed Tracing

* OpenTelemetry instrumentation
* Request lifecycle visualization
* Performance bottleneck analysis
* Trace-to-Logs correlation
* Trace-to-Metrics correlation

### Machine Learning Analytics

* Statistical anomaly detection
* Z-score based anomaly scoring
* Automated severity classification
* Infrastructure behavior analysis

---

## Technology Stack

### AI & Backend

* Python
* FastAPI
* YOLO
* OpenCV
* SQLAlchemy
* SQLite
* Jinja2

### Monitoring & Observability

* Grafana
* Prometheus
* Loki
* Promtail
* Tempo
* OpenTelemetry
* cAdvisor

### DevOps & Deployment

* Docker
* Docker Compose
* Containerized Microservices Architecture

---

## Observability Workflow

The platform enables engineers to move seamlessly between metrics, logs, and traces when investigating issues.

```text
CPU Spike
    ↓
Grafana Metrics
    ↓
Related Trace
    ↓
Associated Logs
    ↓
Root Cause Identification
```

This approach mirrors observability practices used in modern production environments and demonstrates how AI applications can be monitored with the same rigor as enterprise software systems.

---

## Project Goals

* Build a practical AI surveillance application
* Implement a complete observability stack
* Demonstrate modern MLOps practices
* Monitor AI workloads in production-like environments
* Correlate metrics, logs, and traces
* Apply machine learning techniques for anomaly detection
* Create a scalable foundation for intelligent monitoring systems
