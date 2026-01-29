"""
Analytics Data Contracts - Defines how analytics talks to storage and backend

These types serve as the contract between:
  - Storage layer (ingestion, retrieval)
  - Anomaly detection engine
  - Dashboard API

All analytics operations work with these standardized structures.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class MetricPoint:
    """
    Single metric measurement at a specific point in time.
    
    Represents one data point in a time series.
    """
    timestamp: datetime
    value: float
    unit: Optional[str] = None


@dataclass
class MetricSeries:
    """
    Complete time series for a single metric across all observations.
    
    Contract fields (required):
      - tenant_id: Isolates data by organization/customer
      - cluster_id: Groups nodes logically (e.g., production cluster)
      - node_id: Individual machine/server
      - metric_name: Metric identifier (cpu_usage, memory_used, etc.)
      - timestamps: List of observation times (sorted, ascending)
      - values: List of numeric measurements (same length as timestamps)
      - metadata: Additional tags/labels for filtering and context
    
    This is the primary data structure for all analytics operations.
    """
    tenant_id: str
    cluster_id: str
    node_id: str
    metric_name: str
    timestamps: List[datetime]
    values: List[float]
    
    # Optional metadata for richer context
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate data integrity"""
        if len(self.timestamps) != len(self.values):
            raise ValueError(
                f"Timestamp and value count mismatch: "
                f"{len(self.timestamps)} timestamps vs {len(self.values)} values"
            )
        if len(self.timestamps) == 0:
            raise ValueError("MetricSeries must contain at least one data point")
    
    @property
    def length(self) -> int:
        """Number of observations in this series"""
        return len(self.timestamps)
    
    @property
    def time_range(self) -> tuple:
        """(start_time, end_time) for this series"""
        return (self.timestamps[0], self.timestamps[-1])


@dataclass
class AnomalyResult:
    """
    Result of anomaly detection for a single time series or window.
    
    Contract fields (required):
      - tenant_id: Which tenant this anomaly belongs to
      - cluster_id: Which cluster
      - node_id: Which node
      - metric_name: Which metric
      - window_start/window_end: Time range analyzed
      - anomaly_score: Float [0, 1] indicating strength of anomaly
      - anomaly_label: Type of anomaly (spike, trend, seasonal, normal)
      - magnitude: Estimated severity (optional, 0-1 scale)
      - explanation: Free-form explanation (optional)
      - timestamp_detected: When this was computed
    
    Anomaly scores are comparable across metrics and nodes for ranking.
    """
    tenant_id: str
    cluster_id: str
    node_id: str
    metric_name: str
    
    window_start: datetime
    window_end: datetime
    
    anomaly_score: float  # [0, 1] where 1 = strongest anomaly
    anomaly_label: str  # One of: spike, trend, seasonal, normal
    
    magnitude: Optional[float] = None  # [0, 1] severity estimation
    explanation: Optional[str] = None  # Human-readable description
    timestamp_detected: datetime = field(default_factory=datetime.utcnow)
    
    # Engine-specific metadata (for debugging/tracing)
    engine_metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate anomaly score and label"""
        if not (0 <= self.anomaly_score <= 1):
            raise ValueError(f"Anomaly score must be in [0, 1], got {self.anomaly_score}")
        
        valid_labels = {"spike", "trend", "seasonal", "normal"}
        if self.anomaly_label not in valid_labels:
            raise ValueError(
                f"Invalid anomaly label '{self.anomaly_label}'. "
                f"Must be one of: {valid_labels}"
            )
        
        if self.magnitude is not None and not (0 <= self.magnitude <= 1):
            raise ValueError(f"Magnitude must be in [0, 1], got {self.magnitude}")
    
    @property
    def is_anomaly(self) -> bool:
        """Quick check: is this marked as an actual anomaly (not normal)?"""
        return self.anomaly_label != "normal"


@dataclass
class AggregatedAnomalyScore:
    """
    Aggregated anomaly score across a hierarchy level.
    
    Used for ranking nodes within a cluster, clusters within a tenant, etc.
    Enables roll-up analytics for dashboard display.
    """
    tenant_id: str
    cluster_id: Optional[str] = None  # None if aggregating at tenant level
    node_id: Optional[str] = None      # None if aggregating at cluster level
    
    # Aggregation strategy used (max, mean, weighted_mean, etc.)
    aggregation_strategy: str = "max"
    
    # Aggregated score
    aggregate_score: float
    
    # Metadata
    num_metrics_analyzed: int = 0
    num_anomalies_detected: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not (0 <= self.aggregate_score <= 1):
            raise ValueError(
                f"Aggregate score must be in [0, 1], got {self.aggregate_score}"
            )
