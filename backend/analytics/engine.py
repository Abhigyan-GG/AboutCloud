"""
Analytics Anomaly Detection Engine Interface

This module defines the contract for anomaly detection without implementation.
It proves the system is engine-agnostic and allows for future Merlion integration
(or any other detection framework).

Key Design Principle:
  - Backend calls these abstract methods
  - Actual engine (Merlion, Prophet, etc.) is swapped in later
  - No vendor lock-in
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .types import MetricSeries, AnomalyResult


class AnomalyDetectionEngine(ABC):
    """
    Abstract base class for anomaly detection engines.

    Any concrete engine must:
      1. Implement detect() - analyze time series and produce scores
      2. Implement explain() - classify detected anomalies
      3. Be stateless or manage state internally
      4. Return standardized AnomalyResult objects

    Example implementations:
      - MerlionEngine(AnomalyDetectionEngine)
      - ProphetEngine(AnomalyDetectionEngine)
      - IsolationForestEngine(AnomalyDetectionEngine)
    """

    def __init__(self, config: Optional[Dict[str, any]] = None):
        """
        Initialize the detection engine.

        Args:
            config: Engine-specific configuration (threshold, model params, etc.)
        """
        self.config = config or {}

    @abstractmethod
    def detect(
            self,
            time_series: MetricSeries,
            window_size: Optional[int] = None,
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in a time series.

        This is the primary detection interface. It analyzes the input time series
        and returns a list of AnomalyResult objects, one per detection window.

        Contract:
          Input: MetricSeries with valid tenant_id, cluster_id, node_id, metric_name
          Output: List[AnomalyResult] with anomaly_score and anomaly_label populated

        Args:
            time_series: The metric data to analyze (MetricSeries object)
            window_size: Optional override for analysis window size (in data points)
                        If None, use engine default

        Returns:
            List[AnomalyResult]: Anomaly detections sorted by timestamp

        Raises:
            ValueError: If time_series is invalid or too short for analysis
        """
        pass

    @abstractmethod
    def explain(
            self,
            time_series: MetricSeries,
            anomaly_result: AnomalyResult,
    ) -> str:
        """
        Generate a human-readable explanation for a detected anomaly.

        This method takes a previously detected anomaly and provides context:
          - Why it's an anomaly (statistical deviation, pattern break, etc.)
          - How severe it is
          - What specifically changed in the time series

        Contract:
          Input: AnomalyResult from a prior detect() call
          Output: String explanation suitable for dashboard display

        Args:
            time_series: The original metric series being analyzed
            anomaly_result: The anomaly detection result to explain

        Returns:
            str: Human-readable explanation (e.g., "CPU spike: 95% → 99%, +15% deviation")
        """
        pass

    def validate_input(self, time_series: MetricSeries) -> bool:
        """
        Optional: Validate that input time series meets engine requirements.

        Override this in concrete implementations if:
          - Minimum length requirements
          - Frequency/regularity checks
          - Data quality thresholds

        Args:
            time_series: Series to validate

        Returns:
            bool: True if valid, False otherwise
        """
        return True

    @property
    def engine_name(self) -> str:
        """Friendly name for this engine (e.g., 'Merlion', 'Prophet')"""
        return self.__class__.__name__

    @property
    def engine_version(self) -> str:
        """Version identifier (useful for reproducibility)"""
        return "0.0.0-phase1-stub"


class EngineRegistry:
    """
    Simple registry for anomaly detection engines.

    Allows dynamic engine selection at runtime.
    """

    _engines: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, engine_class: type) -> None:
        """Register an engine implementation"""
        cls._engines[name] = engine_class

    @classmethod
    def get(cls, name: str, config: Optional[Dict] = None) -> AnomalyDetectionEngine:
        """Instantiate a registered engine"""
        if name not in cls._engines:
            raise ValueError(
                f"Engine '{name}' not registered. Available: {list(cls._engines.keys())}"
            )
        return cls._engines[name](config)

    @classmethod
    def list_available(cls) -> List[str]:
        """List all registered engine names"""
        return list(cls._engines.keys())


# ============================================================================
# AUTOMATIC ENGINE REGISTRATION
# ============================================================================
# This tries to import and register your concrete implementations safely.
try:
    from .merlion_engine import MerlionAnomalyEngine

    EngineRegistry.register("merlion", MerlionAnomalyEngine)
except ImportError:
    # If the file isn't created yet or Merlion isn't installed, fail silently
    # so the rest of the application doesn't crash.
    pass