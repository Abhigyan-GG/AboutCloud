"""
Analytics Module Initialization

Exposes the primary public API for analytics operations.
"""

from .types import (
    MetricPoint,
    MetricSeries,
    AnomalyResult,
    AggregatedAnomalyScore,
)

from .engine import (
    AnomalyDetectionEngine,
    EngineRegistry,
)

from .windows import (
    SlidingWindowExtractor,
    TimeBasedWindowExtractor,
    TimeWindow,
)

from .aggregation import (
    AggregationStrategy,
    NodeAnomalyAggregator,
    ClusterAnomalyAggregator,
    TenantAnomalyAggregator,
    AggregationPipeline,
    AggregationConfig,
)

from .explain import (
    AnomalyType,
    AnomalyExplanation,
    ExplanationClassifier,
    ExplanationTemplateRegistry,
)

__all__ = [
    # Types
    "MetricPoint",
    "MetricSeries",
    "AnomalyResult",
    "AggregatedAnomalyScore",
    # Engine
    "AnomalyDetectionEngine",
    "EngineRegistry",
    # Windows
    "SlidingWindowExtractor",
    "TimeBasedWindowExtractor",
    "TimeWindow",
    # Aggregation
    "AggregationStrategy",
    "NodeAnomalyAggregator",
    "ClusterAnomalyAggregator",
    "TenantAnomalyAggregator",
    "AggregationPipeline",
    "AggregationConfig",
    # Explanation
    "AnomalyType",
    "AnomalyExplanation",
    "ExplanationClassifier",
    "ExplanationTemplateRegistry",
]

__version__ = "0.1.0-phase1"
__description__ = "Analytics Module - Anomaly Detection Architecture & Plumbing (Phase 1)"
