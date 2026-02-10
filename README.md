# AboutCloud

## Overview

**AboutCloud** is a CloudDet-inspired anomaly analytics platform for monitoring and analyzing cloud performance metrics such as CPU, memory, and disk usage.  
The project is designed as a **multi-tenant, scalable analytics system** that emphasizes **architecture, data lifecycle management, and explainability**, rather than proposing new anomaly detection algorithms.

An existing open-source anomaly detection engine is treated as a **pluggable component**, while the core contribution of AboutCloud lies in:
- analytics orchestration
- hot and cold data storage
- anomaly aggregation and ranking
- interactive monitoring dashboards

---

## Key Objectives

- Ingest time-series performance metrics from multiple tenants
- Detect and rank anomalous behavior across nodes and clusters
- Separate recent (hot) and historical (cold) data storage
- Provide explainable anomaly insights (spike, trend, seasonal)
- Offer a lightweight, interactive dashboard for users and administrators

---

## System Architecture

AboutCloud follows a **modular, layered architecture** with strict separation of concerns:

```
Metric Ingestion
↓
Hot Storage (Time-Series Data)
↓
Analytics Engine (Pluggable)
↓
Aggregation & Ranking
↓
Query APIs
↓
Dashboard (Plain JavaScript)
↓
Cold Storage (Archival)
```

The anomaly detection logic is **engine-agnostic** and can be replaced without impacting the rest of the system.

---

## Project Structure

```
project-root/
├── backend/
│   ├── api/            # REST APIs (ingestion, queries, admin)
│   ├── analytics/      # Anomaly analytics pipeline
│   ├── storage/        # Hot and cold storage logic
│   ├── tenants/        # Tenant and policy models
│   └── main.py
│
├── simulator/          # Metric data generator
│
├── frontend/           # Plain JS dashboard
│
└── README.md
```

---

## Analytics Design

The analytics module is responsible for:
- sliding window extraction over time-series data
- anomaly detection via a pluggable engine
- anomaly explanation (spike, trend, seasonal)
- aggregation of anomaly scores across metrics, nodes, clusters, and tenants

The anomaly detection engine itself is **not implemented from scratch**.  
Instead, AboutCloud focuses on **how anomaly detection results are orchestrated, interpreted, and surfaced to users**.

---

## Multi-Tenant Model

AboutCloud supports multiple tenants using a hierarchical data model:

```
Tenant
└── Cluster
└── Node
└── Metrics (time series)
```

All ingestion, analytics, and queries are **tenant-aware by design**.

---

## Tech Stack

### Backend
- Python (FastAPI / Flask)
- REST-based APIs
- Modular analytics orchestration

### Analytics
- Sliding window time-series analysis
- Pluggable anomaly detection engine (e.g., Merlion)
- Configurable aggregation and ranking strategies

### Storage
- Hot storage: relational or time-series database
- Cold storage: file-based archival (e.g., Parquet)

### Frontend
- Plain HTML, CSS, and JavaScript
- Lightweight charting libraries

---

## Project Phases

### Phase 1 — Architecture & Plumbing
- Define overall system architecture
- Finalize tenant and data models
- Create analytics and backend scaffolding

### Phase 2 — Data Ingestion
- Implement tenant-aware ingestion APIs
- Integrate metric simulator
- Store incoming metrics in hot storage

### Phase 3 — Real Anomaly Detection
- Integrate anomaly detection engine
- Implement sliding window execution
- Compute, store, and aggregate anomaly scores

### Phase 4 — API + Dashboard
- Expose analytics and ranking APIs
- Build interactive dashboard views
- Enable anomaly exploration and drill-down

### Phase 5 — Production Readiness
- Implement hot-to-cold data archival
- Add admin and system health monitoring
- Performance tuning and stability checks

---

## Team Roles & Contributors

- **Analytics Lead — @Abhigyan-GG**  
  Responsible for anomaly analytics orchestration, aggregation, ranking, and explanation logic.

- **Backend Lead — @Saivats**  
  Responsible for ingestion pipelines, storage layers, scheduling, and core APIs.

- **Dashboard / UI Lead — @vabhravi**  
  Responsible for frontend dashboard design, visualizations, and user interactions.

---

## Academic Positioning

AboutCloud emphasizes **system-level design and analytics architecture** rather than algorithmic novelty.  
The project demonstrates how existing anomaly detection techniques can be integrated into a **scalable, explainable, and multi-tenant cloud analytics platform**, making it suitable for academic evaluation and practical understanding.

---

## License

This project is developed as part of an academic course project.

---
