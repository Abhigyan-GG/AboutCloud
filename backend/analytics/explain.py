"""
Anomaly Explanation Classifier

Implements statistical logic to categorize detected anomalies into SPIKE, TREND,
or SEASONAL patterns, and generates human-readable explanations.
"""

from enum import Enum
import statistics
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from .types import MetricSeries, AnomalyResult


class AnomalyType(Enum):
    SPIKE = "spike"
    TREND = "trend"
    SEASONAL = "seasonal"
    NORMAL = "normal"


@dataclass
class AnomalyExplanation:
    anomaly_type: AnomalyType

    # Statistics
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    deviation_percent: Optional[float] = None

    # Severity
    confidence: float = 0.5
    severity: float = 0.5

    # Context
    description: str = ""
    additional_context: Dict[str, any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        return self.severity >= 0.7 and self.confidence >= 0.6


class SpikeDetector:
    """Detects spikes using Z-Score statistical analysis."""

    @staticmethod
    def is_spike(
        values: List[float],
        baseline: float,
        threshold: float = 2.0,
    ) -> bool:
        if len(values) < 3:
            return False

        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            return False

        if stdev == 0:
            return False

        # Find the peak deviation
        max_val = max(values, key=lambda x: abs(x - baseline))

        # Calculate Z-score
        z_score = abs(max_val - baseline) / stdev
        return z_score > threshold


class TrendDetector:
    """Detects trends by comparing the averages of the first and second halves of the window."""

    @staticmethod
    def detect_trend(values: List[float]) -> Optional[str]:
        if len(values) < 4:
            return None

        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid
        second_half_avg = sum(values[mid:]) / (len(values) - mid)

        diff = second_half_avg - first_half_avg

        # If the difference is greater than 5% of the baseline, it's a trend
        threshold = 0.05 * abs(first_half_avg) if first_half_avg != 0 else 0.05

        if abs(diff) > threshold:
            return "up" if diff > 0 else "down"
        return None


class SeasonalityDetector:
    """Detects seasonality by counting mean-crossings to identify cyclic behavior."""

    @staticmethod
    def detect_seasonality(values: List[float]) -> bool:
        if len(values) < 6:
            return False

        mean_val = sum(values) / len(values)

        # Count how many times the data crosses the mean
        crossings = sum(
            1 for i in range(1, len(values))
            if (values[i-1] - mean_val) * (values[i] - mean_val) < 0
        )

        # If it crosses frequently without trending, it's cyclic/seasonal
        return crossings >= 3


@dataclass
class ExplanationTemplate:
    anomaly_type: AnomalyType
    template: str

    def render(self, explanation: AnomalyExplanation) -> str:
        try:
            return self.template.format(
                baseline=explanation.baseline_value,
                observed=explanation.observed_value,
                deviation_percent=explanation.deviation_percent,
                type=explanation.anomaly_type.value,
            )
        except (KeyError, ValueError):
            return self.template


class ExplanationTemplateRegistry:
    _templates: Dict[AnomalyType, ExplanationTemplate] = {
        AnomalyType.SPIKE: ExplanationTemplate(
            anomaly_type=AnomalyType.SPIKE,
            template=(
                "Spike detected: value jumped to {observed:.2f} "
                "({deviation_percent:.1f}% deviation from baseline {baseline:.2f}). "
                "This represents a sudden, temporary abnormality."
            ),
        ),
        AnomalyType.TREND: ExplanationTemplate(
            anomaly_type=AnomalyType.TREND,
            template=(
                "Trend detected: metric shows sustained directional change. "
                "Current peak {observed:.2f} deviates {deviation_percent:.1f}% "
                "from expected {baseline:.2f}."
            ),
        ),
        AnomalyType.SEASONAL: ExplanationTemplate(
            anomaly_type=AnomalyType.SEASONAL,
            template=(
                "Seasonal anomaly: cycle deviation detected. "
                "Value {observed:.2f} breaks expected pattern (baseline {baseline:.2f}, "
                "{deviation_percent:.1f}% off)."
            ),
        ),
        AnomalyType.NORMAL: ExplanationTemplate(
            anomaly_type=AnomalyType.NORMAL,
            template="No anomaly detected. Value {observed:.2f} is within normal range.",
        ),
    }

    @classmethod
    def get_template(cls, anomaly_type: AnomalyType) -> ExplanationTemplate:
        return cls._templates.get(
            anomaly_type,
            ExplanationTemplate(anomaly_type=anomaly_type, template="Anomaly detected.")
        )


class ExplanationClassifier:
    """
    Coordinates the classification logic by testing the data against all detectors.
    """

    def __init__(self):
        pass

    def classify(
        self,
        metric_series: MetricSeries,
        anomaly_result: AnomalyResult,
    ) -> AnomalyExplanation:

        values = metric_series.values
        if not values:
            return AnomalyExplanation(anomaly_type=AnomalyType.NORMAL)

        # Calculate statistics
        baseline = sum(values) / len(values)
        observed = max(values, key=lambda x: abs(x - baseline))

        deviation_percent = ((observed - baseline) / baseline * 100) if baseline != 0 else 0.0

        anomaly_type = AnomalyType.NORMAL

        # Only classify if the engine actually flagged it as an anomaly
        if anomaly_result.anomaly_score >= 0.5:
            if SpikeDetector.is_spike(values, baseline):
                anomaly_type = AnomalyType.SPIKE
            elif TrendDetector.detect_trend(values):
                anomaly_type = AnomalyType.TREND
            elif SeasonalityDetector.detect_seasonality(values):
                anomaly_type = AnomalyType.SEASONAL
            else:
                # Fallback if the ML engine caught it but stats missed it
                anomaly_type = AnomalyType.SPIKE

        # Create the explanation object
        explanation = AnomalyExplanation(
            anomaly_type=anomaly_type,
            baseline_value=baseline,
            observed_value=observed,
            deviation_percent=deviation_percent,
            confidence=anomaly_result.anomaly_score,
            severity=anomaly_result.magnitude or anomaly_result.anomaly_score
        )

        # Generate the human-readable text
        template = ExplanationTemplateRegistry.get_template(anomaly_type)
        explanation.description = template.render(explanation)

        # Update the original AnomalyResult with the newly discovered context
        anomaly_result.anomaly_label = anomaly_type.value
        anomaly_result.explanation = explanation.description

        return explanation

    def classify_batch(
        self,
        metric_series: MetricSeries,
        anomaly_results: List[AnomalyResult],
    ) -> List[AnomalyExplanation]:
        return [self.classify(metric_series, result) for result in anomaly_results]