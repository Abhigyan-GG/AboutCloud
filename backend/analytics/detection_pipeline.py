"""
Detection Pipeline - Orchestrate the end-to-end anomaly detection flow

Flow: MetricSeries → Engine.detect() → Aggregation → Storage
"""

import sys
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .types import MetricSeries, AnomalyResult
from .engine import AnomalyDetectionEngine
from .explain import ExplanationClassifier, ExplanationTemplateRegistry
from .aggregation import (
    NodeAnomalyAggregator,
    ClusterAnomalyAggregator,
    TenantAnomalyAggregator,
)
from .config import get_config
from backend.storage.interface import get_storage


@dataclass
class DetectionPipelineStats:
    """Statistics from detection run"""
    metrics_processed: int = 0
    anomalies_detected: int = 0
    critical_anomalies: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AnomalyDetectionPipeline:
    """
    End-to-end anomaly detection pipeline.

    Steps:
    1. Fetch MetricSeries from storage
    2. Run detection engine
    3. Classify anomalies
    4. Generate explanations
    5. Aggregate scores
    6. Store results
    7. Return statistics
    """

    def __init__(
            self,
            engine: AnomalyDetectionEngine,
            classifier: Optional[ExplanationClassifier] = None,
            storage_backend=None,
    ):
        """
        Initialize pipeline.

        Args:
            engine: AnomalyDetectionEngine implementation
            classifier: ExplanationClassifier (optional)
            storage_backend: StorageBackend for persistence (optional)
        """
        self.engine = engine
        self.classifier = classifier or ExplanationClassifier()
        self.storage = storage_backend
        self.config = get_config()

    def detect_metric(
            self,
            metric_series: MetricSeries,
    ) -> tuple:
        """
        Run detection on a single metric.

        Returns:
            (AnomalyResult list, explanation list, stats)
        """

        stats = DetectionPipelineStats(metrics_processed=1)

        try:
            # 1. Run detection engine
            anomaly_results = self.engine.detect(metric_series)
            stats.anomalies_detected = len(anomaly_results)

            # 2. Classify and explain anomalies
            explanations = []
            critical_count = 0

            for result in anomaly_results:
                # Generate explanation
                explanation = self.classifier.classify(metric_series, result)
                explanations.append(explanation)

                # Count critical anomalies
                if explanation.is_critical:
                    critical_count += 1

                # Add explanation to result
                template = ExplanationTemplateRegistry.get_template(explanation.anomaly_type)
                result.explanation = template.render(explanation)

            stats.critical_anomalies = critical_count

            # 3. Store results if storage configured
            if self.storage:
                for result in anomaly_results:
                    self.storage.store_anomaly_result(
                        tenant_id=metric_series.tenant_id,
                        cluster_id=metric_series.cluster_id,
                        node_id=metric_series.node_id,
                        metric_name=metric_series.metric_name,
                        result=result,
                    )

            return anomaly_results, explanations, stats

        except Exception as e:
            stats.errors.append(f"Detection failed: {str(e)}")
            return [], [], stats

    def detect_cluster(
            self,
            tenant_id: str,
            cluster_id: str,
            node_ids: List[str],
            metric_names: List[str],
    ):
        """
        Run detection across a cluster of nodes.

        Returns results aggregated by node and cluster.
        """

        all_results = []
        stats = DetectionPipelineStats()

        storage = self.storage or get_storage()

        try:
            # Fetch and process each node's metrics
            for node_id in node_ids:
                for metric_name in metric_names:
                    try:
                        # Fetch metric from storage
                        series = storage.get_metric_series(
                            tenant_id=tenant_id,
                            cluster_id=cluster_id,
                            node_id=node_id,
                            metric_name=metric_name,
                            start_time=datetime.min,  # Full range
                            end_time=datetime.max,
                        )

                        # Detect anomalies
                        results, _, metric_stats = self.detect_metric(series)
                        all_results.extend(results)

                        stats.metrics_processed += metric_stats.metrics_processed
                        stats.anomalies_detected += metric_stats.anomalies_detected
                        stats.critical_anomalies += metric_stats.critical_anomalies
                        stats.errors.extend(metric_stats.errors)

                    except Exception as e:
                        stats.errors.append(f"{node_id}/{metric_name}: {e}")

            # Aggregate results
            aggregator = ClusterAnomalyAggregator()
            aggregated_score = aggregator.aggregate(
                results=all_results,
                tenant_id=tenant_id,
                cluster_id=cluster_id,
            )

            # Store aggregated score
            if self.storage:
                self.storage.store_aggregated_score(aggregated_score)

            return all_results, aggregated_score, stats

        except Exception as e:
            stats.errors.append(f"Cluster detection failed: {e}")
            return [], None, stats