# PHASE 1 – QUICK START GUIDE

## 📋 Files Overview

### Core Analytics Module (`backend/analytics/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| **types.py** | Data contracts | `MetricSeries`, `AnomalyResult`, `AggregatedAnomalyScore` |
| **engine.py** | Engine abstraction | `AnomalyDetectionEngine`, `EngineRegistry` |
| **windows.py** | Window extraction | `SlidingWindowExtractor`, `TimeWindow` |
| **aggregation.py** | Multi-level aggregation | `NodeAnomalyAggregator`, `ClusterAnomalyAggregator`, `AggregationPipeline` |
| **explain.py** | Explanation scaffold | `AnomalyType`, `ExplanationClassifier` |
| **README.md** | Module documentation | System overview, design decisions |
| **INTEGRATION_CONTRACT.py** | Backend specification | `get_metric_series()` interface |
| **__init__.py** | Public API | All exports |

### Documentation Files

| File | Purpose |
|------|---------|
| `PHASE1_COMPLETION.md` | Detailed checklist ✅ |
| `PHASE1_FINAL_REPORT.md` | Executive summary & roadmap |
| `verify_phase1.py` | Validation test script |

---

## 🚀 Quick Start (60 seconds)

### 1. Understand the Architecture
```bash
# Read the main documentation
cat backend/analytics/README.md
```

### 2. Check Data Contracts
```bash
# View the data types
less backend/analytics/types.py
```

### 3. Review Integration Requirements
```bash
# See what backend needs to provide
less backend/analytics/INTEGRATION_CONTRACT.py
```

### 4. Validate Everything Works
```bash
# Run verification script
python verify_phase1.py
```

---

## 📊 System Architecture

```
Storage (Hot/Cold)
        ↓
    get_metric_series()
        ↓
[Analytics Module - Phase 1 ✅]
    ├─ Window extraction
    ├─ Anomaly detection interface
    ├─ Multi-level aggregation
    └─ Explanation scaffold
        ↓
    store_anomaly_results()
        ↓
Results Storage
        ↓
Dashboard APIs (Phase 2)
        ↓
Frontend UI
```

---

## 🔑 Key Concepts

### 1. Data Contracts
- **MetricSeries**: Time series with tenant/cluster/node context
- **AnomalyResult**: Detection output with score (0-1) and label
- **AggregatedAnomalyScore**: Ranking scores for nodes/clusters

### 2. Engine Abstraction
- Abstract `AnomalyDetectionEngine` class
- No implementation yet (Merlion comes in Phase 2)
- Allows any engine to be plugged in

### 3. Multi-Level Aggregation
- Metric → Node (combine metrics)
- Node → Cluster (rank nodes)
- Cluster → Tenant (system health)

### 4. Strategies
- **MAX**: "Is anything anomalous?"
- **MEAN**: "What's the overall health?"
- **WEIGHTED**: "Some metrics matter more"
- **P95**: "What's the real problem?"

---

## 📝 Code Examples

### Create a Metric Series
```python
from datetime import datetime
from backend.analytics import MetricSeries

series = MetricSeries(
    tenant_id="acme-corp",
    cluster_id="prod-us-east",
    node_id="node-042",
    metric_name="cpu_usage",
    timestamps=[
        datetime(2025, 1, 1, 0, 0),
        datetime(2025, 1, 1, 0, 1),
        # ... more timestamps
    ],
    values=[50.0, 55.0, ...],  # Aligned with timestamps
)
```

### Extract Windows
```python
from backend.analytics import SlidingWindowExtractor

extractor = SlidingWindowExtractor(
    window_size_points=100,
    stride_points=50,  # 50% overlap
)
windows = extractor.extract(series)
```

### Aggregate Scores
```python
from backend.analytics import NodeAnomalyAggregator, AggregationStrategy

aggregator = NodeAnomalyAggregator(
    strategy=AggregationStrategy.MAX
)
node_score = aggregator.aggregate(anomaly_results)
print(f"Node {node_score.node_id}: {node_score.aggregate_score}")
```

### Create Anomaly Result
```python
from backend.analytics import AnomalyResult
from datetime import datetime

result = AnomalyResult(
    tenant_id="acme-corp",
    cluster_id="prod-us-east",
    node_id="node-042",
    metric_name="cpu_usage",
    window_start=datetime(2025, 1, 1),
    window_end=datetime(2025, 1, 1, 1),
    anomaly_score=0.85,  # 85% anomalous
    anomaly_label="spike",  # Type: spike, trend, seasonal, normal
)
```

---

## ✅ Verification Checklist

- [ ] All 8 files exist in `backend/analytics/`
- [ ] `verify_phase1.py` runs successfully
- [ ] Can import: `from backend.analytics import MetricSeries, ...`
- [ ] Type hints are present on all functions
- [ ] Docstrings explain all classes
- [ ] README explains the system
- [ ] INTEGRATION_CONTRACT specifies backend requirements

**All checked? Phase 1 is READY.** 🎉

---

## 🔗 Document Links

| Document | Purpose |
|----------|---------|
| [backend/analytics/README.md](backend/analytics/README.md) | System overview & architecture |
| [backend/analytics/INTEGRATION_CONTRACT.py](backend/analytics/INTEGRATION_CONTRACT.py) | What Phase 2 needs to build |
| [PHASE1_FINAL_REPORT.md](PHASE1_FINAL_REPORT.md) | Executive summary & roadmap |
| [PHASE1_COMPLETION.md](PHASE1_COMPLETION.md) | Detailed checklist |
| [verify_phase1.py](verify_phase1.py) | Validation tests |

---

## 🎯 What's Next?

### For Backend Team
1. Read `INTEGRATION_CONTRACT.py`
2. Implement `get_metric_series()` interface
3. Create database schema for results

### For ML Team
1. Review `engine.py` abstract interface
2. Plan Merlion integration
3. Implement `detect()` and `explain()` methods

### For Dashboard Team
1. Read `README.md` for context
2. Plan query APIs
3. Design aggregation visualization

### For Everyone
1. Understand the data contracts in `types.py`
2. Know the aggregation hierarchy (metric→node→cluster→tenant)
3. Plan integration for Phase 2

---

## 📞 Questions?

- **What does this module do?** → Read `README.md`
- **What's the contract?** → Read `INTEGRATION_CONTRACT.py`
- **How do I use the types?** → See code examples above
- **What about Phase 2?** → Read `PHASE1_FINAL_REPORT.md`

---

## 🏁 Status

✅ **Phase 1: COMPLETE**

- ✅ Architecture defined
- ✅ Data contracts specified
- ✅ Engine abstraction proven
- ✅ Aggregation implemented
- ✅ Documentation comprehensive
- ✅ Ready for Phase 2

**No external dependencies. Zero technical debt. Clear path forward.** 🚀

---

**Created:** January 29, 2025
**Version:** 1.0 (Phase 1 Complete)
