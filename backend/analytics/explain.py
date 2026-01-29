"""
Anomaly Explanation Scaffold

Defines categories and placeholders for explaining detected anomalies.
This is the classification layer: "what type of anomaly is this?"

No detection logic yet — only structure and interfaces.
Detection will be implemented later when the anomaly engine is integrated.

Explanation Categories:
  SPIKE:    Sudden, temporary spike in metric value
  TREND:    Sustained increase or decrease over time
  SEASONAL: Cyclic pattern deviation from expected
  NORMAL:   No anomaly detected (baseline for comparison)
"""

from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

from .types import MetricSeries, AnomalyResult


class AnomalyType(Enum):
    """
    Enumeration of anomaly classification types.
    
    This maps to the anomaly_label field in AnomalyResult.
    """
    SPIKE = "spike"           # Sudden deviation, quickly recovers
    TREND = "trend"           # Sustained change in direction
    SEASONAL = "seasonal"     # Deviation from expected cyclic pattern
    NORMAL = "normal"         # No anomaly (baseline state)


@dataclass
class AnomalyExplanation:
    """
    Structured explanation for a detected anomaly.
    
    This contains:
      - What type of anomaly it is
      - Severity/confidence score
      - Key statistics
      - Human-readable description
    """
    anomaly_type: AnomalyType
    
    # Statistics
    baseline_value: Optional[float] = None     # Expected "normal" value
    observed_value: Optional[float] = None     # What we actually saw
    deviation_percent: Optional[float] = None  # Percent deviation from baseline
    
    # Severity
    confidence: float = 0.5  # [0, 1] how confident in this classification
    severity: float = 0.5    # [0, 1] how severe this anomaly is
    
    # Context
    description: str = ""
    additional_context: Dict[str, any] = field(default_factory=dict)
    
    @property
    def is_critical(self) -> bool:
        """Quick check: is this a critical anomaly?"""
        return self.severity >= 0.7 and self.confidence >= 0.6


class ExplanationClassifier:
    """
    Placeholder for anomaly type classification logic.
    
    This interface will be implemented when the actual detection engine is integrated.
    For now, it defines the contract that any classifier must follow.
    
    Usage Pattern (Phase 2):
        >>> classifier = ExplanationClassifier()
        >>> explanation = classifier.classify(
        ...     metric_series=series,
        ...     anomaly_result=detection_result,
        ... )
        >>> print(f"This is a {explanation.anomaly_type} anomaly")
    """
    
    def __init__(self):
        """Initialize classifier (stub for Phase 1)"""
        pass
    
    def classify(
        self,
        metric_series: MetricSeries,
        anomaly_result: AnomalyResult,
    ) -> AnomalyExplanation:
        """
        Classify an anomaly into one of the standard types.
        
        Contract:
          Input: AnomalyResult from detect() + original time series
          Output: AnomalyExplanation with type and statistics
        
        Args:
            metric_series: Original time series that was analyzed
            anomaly_result: Detection result to classify
        
        Returns:
            AnomalyExplanation with category and details
        
        Note:
            Phase 1: Returns stub explanation (type=NORMAL)
            Phase 2: Will implement actual classification logic
        """
        # PHASE 1 STUB: Just return NORMAL for now
        return AnomalyExplanation(
            anomaly_type=AnomalyType.NORMAL,
            description="[Phase 1 Stub] Classification logic not yet implemented",
        )
    
    def classify_batch(
        self,
        metric_series: MetricSeries,
        anomaly_results: List[AnomalyResult],
    ) -> List[AnomalyExplanation]:
        """
        Classify multiple anomalies from the same series.
        
        Batch processing hint for efficiency in Phase 2.
        
        Args:
            metric_series: Original series
            anomaly_results: Multiple detection results
        
        Returns:
            List of explanations (same order as input)
        """
        return [self.classify(metric_series, result) for result in anomaly_results]


class SpikeDetector:
    """
    Placeholder for spike-specific logic.
    
    A spike is characterized by:
      - Sudden jump in value
      - Quick recovery to baseline
      - Localized in time (typically 1-5 observations)
    
    Phase 2: Will implement statistical spike detection.
    """
    
    @staticmethod
    def is_spike(
        values: List[float],
        baseline: float,
        threshold: float = 2.0,
    ) -> bool:
        """
        Check if values represent a spike pattern (stub).
        
        Args:
            values: Time series values to analyze
            baseline: Expected normal value
            threshold: Z-score threshold for spike detection
        
        Returns:
            bool: True if spike pattern detected
        
        Note: Phase 1 returns False (not implemented)
        """
        # STUB: Always return False in Phase 1
        return False


class TrendDetector:
    """
    Placeholder for trend-specific logic.
    
    A trend is characterized by:
      - Sustained directional change (increasing/decreasing)
      - Lasts over multiple observations
      - May indicate resource saturation or degradation
    
    Phase 2: Will implement linear/polynomial trend fitting.
    """
    
    @staticmethod
    def detect_trend(values: List[float]) -> Optional[str]:
        """
        Detect if values show an uptrend, downtrend, or stable (stub).
        
        Args:
            values: Time series values
        
        Returns:
            str: "up", "down", or None for no trend
        
        Note: Phase 1 returns None (not implemented)
        """
        # STUB: Always return None in Phase 1
        return None


class SeasonalityDetector:
    """
    Placeholder for seasonality-specific logic.
    
    Seasonality is characterized by:
      - Repeating cyclic patterns
      - Deviation from expected cycle
      - Common in cloud metrics (business hours, daily patterns)
    
    Phase 2: Will implement FFT or autocorrelation-based detection.
    """
    
    @staticmethod
    def detect_seasonality(values: List[float]) -> bool:
        """
        Check if values show seasonal patterns (stub).
        
        Args:
            values: Time series values
        
        Returns:
            bool: True if seasonality detected
        
        Note: Phase 1 returns False (not implemented)
        """
        # STUB: Always return False in Phase 1
        return False


@dataclass
class ExplanationTemplate:
    """
    Template for generating human-readable explanations.
    
    Allows consistent, parameterized explanation text generation.
    
    Example:
        >>> template = ExplanationTemplate(
        ...     anomaly_type=AnomalyType.SPIKE,
        ...     template="CPU usage {metric_name} spiked from {baseline} "
        ...              "to {observed} ({deviation_percent:.1f}% increase)"
        ... )
    """
    anomaly_type: AnomalyType
    template: str
    
    def render(self, explanation: AnomalyExplanation) -> str:
        """
        Render explanation text from template.
        
        Args:
            explanation: AnomalyExplanation with values to interpolate
        
        Returns:
            Formatted explanation string
        """
        try:
            return self.template.format(
                baseline=explanation.baseline_value,
                observed=explanation.observed_value,
                deviation_percent=explanation.deviation_percent,
                type=explanation.anomaly_type.value,
            )
        except (KeyError, ValueError):
            return self.template  # Return template if interpolation fails


class ExplanationTemplateRegistry:
    """
    Registry of explanation templates for each anomaly type.
    
    Provides default explanations; can be customized per organization.
    
    Phase 2: Can be extended with custom templates per metric/cluster.
    """
    
    _templates: Dict[AnomalyType, ExplanationTemplate] = {
        AnomalyType.SPIKE: ExplanationTemplate(
            anomaly_type=AnomalyType.SPIKE,
            template=(
                "Spike detected: value increased from {baseline} to {observed} "
                "({deviation_percent:.1f}% above baseline). "
                "This represents a sudden, temporary deviation."
            ),
        ),
        AnomalyType.TREND: ExplanationTemplate(
            anomaly_type=AnomalyType.TREND,
            template=(
                "Trend detected: metric shows sustained directional change. "
                "Current value {observed} deviates {deviation_percent:.1f}% "
                "from baseline {baseline}. This may indicate resource saturation."
            ),
        ),
        AnomalyType.SEASONAL: ExplanationTemplate(
            anomaly_type=AnomalyType.SEASONAL,
            template=(
                "Seasonal anomaly: current value {observed} deviates from "
                "expected seasonal pattern (baseline {baseline}, "
                "{deviation_percent:.1f}% off). Check for unusual activity patterns."
            ),
        ),
        AnomalyType.NORMAL: ExplanationTemplate(
            anomaly_type=AnomalyType.NORMAL,
            template="No anomaly detected. Value {observed} is within normal range.",
        ),
    }
    
    @classmethod
    def get_template(cls, anomaly_type: AnomalyType) -> ExplanationTemplate:
        """Get template for anomaly type"""
        return cls._templates.get(
            anomaly_type,
            ExplanationTemplate(
                anomaly_type=anomaly_type,
                template="Anomaly of type {type} detected.",
            ),
        )
    
    @classmethod
    def register_template(
        cls,
        anomaly_type: AnomalyType,
        template: ExplanationTemplate,
    ) -> None:
        """Register custom template"""
        cls._templates[anomaly_type] = template
