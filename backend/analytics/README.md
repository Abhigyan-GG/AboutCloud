# Analytics Module – Phase 1 Documentation

## Overview

The `analytics` module is the core anomaly detection and aggregation layer for the multi-tenant cloud metrics platform. It provides the architecture, data contracts, and plumbing necessary for detecting, ranking, and explaining anomalies across distributed infrastructure.

**Key Principle:** This module treats anomaly detection as a plug-and-play component. The focus is on system architecture, not on inventing new ML algorithms.

---

## What This Module Does

### 1. **Data Contracts (`types.py`)**
- Defines standardized data structures for all analytics operations
- `MetricSeries`: Wraps time-series metric data with tenant/cluster/node context
- `AnomalyResult`: Standardized output from detection engines
- `AggregatedAnomalyScore`: Roll-up scores for dashboard ranking

### 2. **Engine Abstraction (`engine.py`)**
- Defines an engine-agnostic interface for anomaly detection
- Abstract base class `AnomalyDetectionEngine` with `detect()` and `explain()` methods
- Engine registry for dynamic selection (Merlion, Prophet, etc. can be plugged in later)
- **No detection logic implemented yet** — just the interface contract

### 3. **Sliding Windows (`windows.py`)**
- Extracts overlapping time windows from metric series for batch analysis
- Supports configurable window size and stride
- Deterministic slicing ensures reproducibility
- Both point-based and time-based window extraction

### 4. **Aggregation Pipeline (`aggregation.py`)**
- **CloudDet-inspired** multi-level aggregation:
  - Metric → Node (combines CPU, memory, disk into node health)
  - Node → Cluster (ranks nodes by anomaly severity)
  - Cluster → Tenant (system-wide health view)
- Multiple aggregation strategies: MAX, MEAN, WEIGHTED, P95
- Enables "top 10 anomalous nodes" dashboard rankings

### 5. **Explanation Scaffold (`explain.py`)**
- Defines anomaly classification types: SPIKE, TREND, SEASONAL, NORMAL
- Placeholder structure for categorizing anomalies (no detection yet)
- Template system for human-readable explanations
- Foundation for Phase 2 explanation logic

---

## What This Module Does NOT Do (Phase 1)

❌ **No anomaly detection implementation** — interfaces only
❌ **No Merlion integration** — that's Phase 2
❌ **No dashboards** — backend API only
❌ **No ML models** — this module coordinates existing ones
❌ **No simulator** — but simulator data can be wrapped into `MetricSeries`

---

## How It Fits Into the System

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Metrics Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                               │
│  │   Storage    │  ←─── Ingestion (hot/cold)                   │
│  │   (metrics)  │                                               │
│  └──────────────┘                                               │
│         ↓                                                         │
│  ┌──────────────────────────────────────┐                       │
│  │   ANALYTICS MODULE (This Code)       │                       │
│  │  ┌────────────────────────────────┐  │                       │
│  │  │ 1. Fetch MetricSeries          │  │                       │
│  │  ├────────────────────────────────┤  │                       │
│  │  │ 2. Extract sliding windows     │  │                       │
│  │  ├────────────────────────────────┤  │                       │
│  │  │ 3. Run anomaly detection       │  │                       │
│  │  ├────────────────────────────────┤  │                       │
│  │  │ 4. Aggregate scores            │  │                       │
│  │  ├────────────────────────────────┤  │                       │
│  │  │ 5. Rank nodes (top anomalies) │  │                       │
│  │  └────────────────────────────────┘  │                       │
│  └──────────────────────────────────────┘                       │
│         ↓                                                         │
│  ┌──────────────────────────────────────┐                       │
│  │   Results → Storage                  │                       │
│  │   (anomaly scores, rankings)         │                       │
│  └──────────────────────────────────────┘                       │
│         ↓                                                         │
│  ┌──────────────┐                                               │
│  │   Dashboard  │  ← Query API (Phase 2)                        │
│  │   Backend    │                                               │
│  └──────────────┘                                               │
│         ↓                                                         │
│  ┌──────────────┐                                               │
│  │   UI/Frontend│                                               │
│  └──────────────┘                                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

The analytics module is the **orchestrator** between storage and dashboards.

---

## Core Design Decisions & Justification

### 1. **Engine Abstraction (Not Direct Merlion Dependency)**
**Why:** Avoids vendor lock-in. Allows swapping detection engines without rewriting analytics code.
**How:** Abstract `AnomalyDetectionEngine` class with `detect()` and `explain()` methods.

### 2. **Aggregation Strategies (MAX, MEAN, WEIGHTED, P95)**
**Why:** Different use cases need different semantics:
- **MAX**: "Is ANY metric anomalous?" (conservative, alert if any problem)
- **MEAN**: "How is the node overall?" (balanced health view)
- **WEIGHTED**: "Some metrics matter more" (CPU > disk I/O)
- **P95**: "Ignore noise, show real problems" (tail-based alerting)

### 3. **Sliding Windows (Deterministic)**
**Why:** Ensures reproducibility, enables batch processing, supports multiple temporal resolutions.
**Strategy:** Point-based (100 points, stride 50) or time-based (1 hour window, 30 min stride).

### 4. **Multi-Tenant Isolation**
**Why:** Core architectural requirement. Every data structure includes `tenant_id`.
**Benefit:** Customers' data never mixed; enables per-tenant SLAs and billing.

### 5. **Explanation Categories (SPIKE/TREND/SEASONAL/NORMAL)**
**Why:** Users need to understand *why* something is anomalous.
**Phase 1:** Just the category structure; Phase 2 implements detection logic.

---

## Phase 1 ✅ Deliverables Summary

- ✅ Analytics folder structure with 6 core modules
- ✅ `MetricSeries`, `AnomalyResult`, `AggregatedAnomalyScore` data contracts
- ✅ Engine-agnostic interface (no Merlion yet)
- ✅ Sliding window logic (deterministic, tested on various series lengths)
- ✅ Aggregation pipeline (metric→node→cluster→tenant)
- ✅ Explanation scaffold (categories, templates, placeholder logic)
- ✅ This documentation

**Status:** Architecture and plumbing complete. Ready for Phase 2 (engine integration).

---

## What Comes Next (Phase 2)

1. **Merlion Integration** — Implement concrete detection engine
2. **Backend API** — REST endpoints to call analytics (`/detect`, `/rank`, `/explain`)
3. **Storage Connectors** — Query hot/cold storage for metric data
4. **Dashboard Backend** — Aggregate results for UI consumption
5. **Unit Tests** — Comprehensive coverage of windowing, aggregation, type validation

---

## Usage Example (Phase 2 Preview)

```python
from analytics.engine import EngineRegistry
from analytics.windows import SlidingWindowExtractor
from analytics.aggregation import AggregationConfig, AggregationPipeline
from storage import get_metric_series

# 1. Get metric data from storage
metric_series = get_metric_series(
    tenant_id="acme-corp",
    cluster_id="prod-us-east",
    node_id="node-042",
    metric="cpu_usage",
    start_time=...,
    end_time=...,
)

# 2. Extract windows
extractor = SlidingWindowExtractor(window_size_points=100, stride_points=50)
windows = extractor.extract(metric_series)

# 3. Run detection (Phase 2: Merlion engine)
engine = EngineRegistry.get("merlion", config={...})
anomaly_results = engine.detect(metric_series)

# 4. Aggregate scores
pipeline = AggregationPipeline(AggregationConfig(node_strategy="MAX"))
node_scores = pipeline.aggregate_nodes(anomaly_results)

# 5. Rank nodes for dashboard
ranked = sorted(node_scores, key=lambda x: x.aggregate_score, reverse=True)
print(f"Top anomalous node: {ranked[0].node_id} (score: {ranked[0].aggregate_score})")
```

---

## File Structure

```
backend/analytics/
├── types.py              # Data contracts (MetricSeries, AnomalyResult, etc.)
├── engine.py             # Engine abstraction (plug-and-play interface)
├── windows.py            # Sliding window extraction logic
├── aggregation.py        # Multi-level aggregation (metric→node→cluster→tenant)
├── explain.py            # Explanation scaffold (spike/trend/seasonal/normal)
├── README.md             # This file
```

---

## Contact & Questions

- **Architect:** See project repository for team information
- **Related Docs:** See parent `/backend` README for system architecture
