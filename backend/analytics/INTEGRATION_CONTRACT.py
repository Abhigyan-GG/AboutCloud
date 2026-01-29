"""
BACKEND INTEGRATION CONTRACT

This file documents the interface between the backend (storage layer) and 
the analytics module. It defines how data flows from storage into analytics
and how results flow back out.

This is NOT implementation — just the contract specification.
"""

from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

# Import analytics types
from .types import MetricSeries, MetricPoint


# ============================================================================
# PRIMARY STORAGE INTERFACE
# ============================================================================

def get_metric_series(
    tenant_id: str,
    cluster_id: str,
    node_id: str,
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
) -> MetricSeries:
    """
    REQUIRED: Backend must implement this function.
    
    Retrieves a time series of metric data from storage (hot or cold).
    
    This is the PRIMARY data input to the analytics module.
    
    Contract:
      Input:  Tenant/cluster/node identifiers + metric name + time range
      Output: MetricSeries object with timestamps and values populated
      
    Args:
        tenant_id: Unique identifier for the customer/organization
                  Example: "acme-corp-prod"
        
        cluster_id: Identifies a logical cluster of nodes
                   Example: "prod-us-east-1"
        
        node_id: Identifies a specific machine/server
                Example: "node-042" or "i-1234567890abcdef0"
        
        metric_name: Name of the metric to fetch
                    Example: "cpu_usage", "memory_used", "disk_io_read"
        
        start_time: Beginning of time range (inclusive)
                   Must be timezone-aware (UTC preferred)
        
        end_time: End of time range (inclusive)
                 Must be >= start_time
    
    Returns:
        MetricSeries object with:
          - tenant_id, cluster_id, node_id, metric_name: populated
          - timestamps: sorted list of datetime objects (ascending)
          - values: corresponding float values (same length as timestamps)
          - metadata: optional tags/context
    
    Raises:
        ValueError: If time range is invalid or empty
        KeyError: If tenant/cluster/node/metric not found
        RuntimeError: If storage access fails
    
    Example:
        >>> series = get_metric_series(
        ...     tenant_id="acme-corp",
        ...     cluster_id="prod-us-east",
        ...     node_id="node-042",
        ...     metric_name="cpu_usage",
        ...     start_time=datetime(2025, 1, 1),
        ...     end_time=datetime(2025, 1, 2),
        ... )
        >>> print(f"Fetched {len(series.timestamps)} data points")
        >>> for ts, val in zip(series.timestamps, series.values):
        ...     print(f"{ts}: {val}%")
    
    Storage Location Selection (Implementation Detail):
        - Recent data (< 7 days): Fetch from HOT storage (fast)
        - Older data (> 7 days): Fetch from COLD storage (slower)
        - This function should abstract this away from analytics
    
    Data Format Requirements:
        - Timestamps: Must be timezone-aware (utc preferred)
        - Timestamps: Must be in ascending order
        - Values: Float type (handle NaN/Inf gracefully)
        - Values: Should match metric units (percentages, bytes, etc.)
    
    Performance Requirements:
        - Max 5 second latency for hot storage queries
        - Acceptable latency for cold storage: 30-60 seconds
    """
    # STUB: This will be implemented in Phase 2
    # For now, this documents what backend must provide
    raise NotImplementedError("Backend must implement get_metric_series()")


# ============================================================================
# ALTERNATIVE/BATCH INTERFACES (Optional for Phase 1)
# ============================================================================

def get_metric_series_batch(
    tenant_id: str,
    cluster_id: str,
    node_ids: List[str],
    metric_names: List[str],
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """
    OPTIONAL: Batch version for efficiency.
    
    Retrieve multiple metric series at once.
    
    Returns:
        Dict mapping (node_id, metric_name) → MetricSeries
        Example: {
            ("node-042", "cpu_usage"): MetricSeries(...),
            ("node-042", "memory_used"): MetricSeries(...),
            ("node-043", "cpu_usage"): MetricSeries(...),
        }
    
    Benefit: Allows backend to batch-fetch from storage (more efficient).
    """
    raise NotImplementedError("Optional: Backend may implement for performance")


# ============================================================================
# RESULTS STORAGE INTERFACE
# ============================================================================

def store_anomaly_results(
    anomaly_results: List['AnomalyResult'],  # From analytics.types
) -> None:
    """
    REQUIRED (Phase 2): Store anomaly detection results.
    
    Analytics produces AnomalyResult objects. Backend must store them
    so they can be queried by dashboards later.
    
    Args:
        anomaly_results: List of AnomalyResult objects from detection engine
    
    Storage Strategy:
        - Results go to HOT storage (queries within seconds)
        - Keep recent results (last 7-30 days)
        - Archive older results to COLD storage if desired
        - Index by: (tenant_id, cluster_id, timestamp)
        - Allow range queries: all anomalies for cluster in time window
    
    Example Schema (SQL):
        CREATE TABLE anomaly_results (
            id BIGINT PRIMARY KEY,
            tenant_id VARCHAR,
            cluster_id VARCHAR,
            node_id VARCHAR,
            metric_name VARCHAR,
            window_start TIMESTAMP,
            window_end TIMESTAMP,
            anomaly_score FLOAT,
            anomaly_label VARCHAR,
            magnitude FLOAT,
            explanation TEXT,
            timestamp_detected TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            INDEX idx_tenant_cluster (tenant_id, cluster_id),
            INDEX idx_time (window_start, window_end)
        );
    """
    raise NotImplementedError("Phase 2: Backend will implement result storage")


def get_anomaly_results(
    tenant_id: str,
    cluster_id: Optional[str] = None,
    node_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> List['AnomalyResult']:
    """
    REQUIRED (Phase 2): Query stored anomaly results.
    
    Dashboard and queries will fetch anomaly results via this interface.
    
    Args:
        tenant_id: Required
        cluster_id: Optional filter
        node_id: Optional filter
        metric_name: Optional filter
        start_time: Optional time range start
        end_time: Optional time range end
        limit: Max results to return
    
    Returns:
        List of AnomalyResult objects matching filters
    
    Example:
        >>> results = get_anomaly_results(
        ...     tenant_id="acme-corp",
        ...     cluster_id="prod-us-east",
        ...     start_time=datetime(2025, 1, 1),
        ...     end_time=datetime(2025, 1, 2),
        ...     limit=100,
        ... )
    """
    raise NotImplementedError("Phase 2: Backend will implement result queries")


def store_aggregated_scores(
    scores: List['AggregatedAnomalyScore'],  # From analytics.types
) -> None:
    """
    OPTIONAL: Store pre-aggregated scores for faster dashboard queries.
    
    Instead of querying raw anomaly results and aggregating on-the-fly,
    backend can store pre-computed aggregations.
    
    Example Use Case:
        - Every 5 minutes, compute top-10 anomalous nodes per cluster
        - Store these pre-computed scores
        - Dashboard queries these instead of raw results
        - Trades storage for query speed
    """
    raise NotImplementedError("Optional optimization for Phase 2")


# ============================================================================
# DATA EXPECTATIONS FOR SIMULATOR
# ============================================================================

@dataclass
class SimulatorMetricOutput:
    """
    Expected format of data from the simulator/synthetic data generator.
    
    Simulator produces this; it needs to be converted to MetricSeries
    before analytics can use it.
    """
    timestamp: datetime
    value: float
    metadata: dict = None


def wrap_simulator_output(
    simulator_data: List[SimulatorMetricOutput],
    tenant_id: str,
    cluster_id: str,
    node_id: str,
    metric_name: str,
) -> MetricSeries:
    """
    Helper function to convert simulator output to MetricSeries.
    
    Ensures simulated anomalies can be detected by analytics.
    
    Args:
        simulator_data: List of SimulatorMetricOutput
        tenant_id, cluster_id, node_id, metric_name: Metadata
    
    Returns:
        MetricSeries ready for anomaly detection
    
    Example:
        >>> simulated = simulate_metrics(
        ...     num_points=1000,
        ...     anomalies=["spike_at_500", "trend_500_600"]
        ... )
        >>> series = wrap_simulator_output(
        ...     simulated,
        ...     tenant_id="test-tenant",
        ...     cluster_id="test-cluster",
        ...     node_id="test-node",
        ...     metric_name="cpu_usage",
        ... )
        >>> results = engine.detect(series)
        >>> assert len(results) > 0  # Anomalies detected
    """
    timestamps = [item.timestamp for item in simulator_data]
    values = [item.value for item in simulator_data]
    
    return MetricSeries(
        tenant_id=tenant_id,
        cluster_id=cluster_id,
        node_id=node_id,
        metric_name=metric_name,
        timestamps=timestamps,
        values=values,
        metadata=simulator_data[0].metadata or {},
    )


# ============================================================================
# DATA FLOW SUMMARY
# ============================================================================

"""
ANALYTICS DATA FLOW:

┌──────────────┐
│   Storage    │  (Hot/Cold)
│   (metrics)  │
└──────┬───────┘
       │
       │ get_metric_series(tenant_id, cluster_id, node_id, metric, start, end)
       ↓
┌──────────────────────────────────────┐
│  Analytics Module                    │
│  ┌────────────────────────────────┐  │
│  │ 1. Extract windows             │  │
│  │ 2. Run detection engine        │  │
│  │ 3. Classify anomalies          │  │
│  │ 4. Aggregate scores            │  │
│  │ 5. Rank nodes/clusters         │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────────────────┘
       │
       │ store_anomaly_results(results)
       │ store_aggregated_scores(aggregations)
       ↓
┌──────────────┐
│   Storage    │  (Results)
│   (anomalies)│
└──────┬───────┘
       │
       │ Dashboard Backend queries results
       ↓
┌──────────────┐
│   Dashboard  │
│   Frontend   │
└──────────────┘

"""

# ============================================================================
# MULTI-TENANT ISOLATION CONTRACT
# ============================================================================

"""
CRITICAL: Multi-Tenant Data Isolation

Every data structure includes tenant_id:
  - MetricSeries.tenant_id
  - AnomalyResult.tenant_id
  - AggregatedAnomalyScore.tenant_id

Storage MUST enforce:
  1. Tenant A cannot query tenant B's metrics
  2. Tenant A cannot see tenant B's anomaly results
  3. Aggregations are never cross-tenant
  4. Billing/usage tracking is per-tenant

This is NOT optional — it's architectural.
"""

# ============================================================================
# PHASE 1 vs PHASE 2 RESPONSIBILITY
# ============================================================================

"""
PHASE 1 (Current):
  ✅ Analytics Module defines contracts
  ✅ Data types are defined
  ✅ Interfaces are specified (abstract methods)
  ❌ Backend doesn't need to implement yet
  ❌ No actual data flows

PHASE 2 (Next):
  ✅ Backend implements get_metric_series()
  ✅ Anomaly engine produces results
  ✅ Backend stores results
  ✅ Dashboard queries results

This file documents what Phase 2 needs. Phase 1 is just architecture.
"""
