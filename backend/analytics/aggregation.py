"""
Anomaly Aggregation Logic

Implements multi-level aggregation of anomaly scores across the system hierarchy:
  metric → node → cluster → tenant

This enables:
  - Ranking nodes by "abnormality"
  - Dashboard roll-ups (show top 10 anomalous nodes)
  - SLA violation detection at cluster/tenant level
  - Historical trending of system health

Design Principle (CloudDet-inspired):
  Use simple, deterministic aggregation strategies (max, mean, weighted).
  Complex ranking happens at query time, not ingestion.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .types import AnomalyResult, AggregatedAnomalyScore


class AggregationStrategy(Enum):
    """
    Supported aggregation strategies for combining anomaly scores.
    
    MAX:       Use the highest anomaly score seen
               Rationale: One severe anomaly = one bad node
    
    MEAN:      Average all anomaly scores
               Rationale: Overall system health perspective
    
    WEIGHTED:  Weighted average by metric importance
               Rationale: Not all metrics are equally important
    
    P95:       Use 95th percentile
               Rationale: Ignore noise, focus on real problems
    """
    MAX = "max"
    MEAN = "mean"
    WEIGHTED = "weighted"
    P95 = "p95"


class NodeAnomalyAggregator:
    """
    Aggregates anomaly scores for a single node across all its metrics.
    
    Input: List[AnomalyResult] where all results are for the same node
    Output: Single AggregatedAnomalyScore for that node
    
    Example Usage:
        >>> aggregator = NodeAnomalyAggregator(strategy=AggregationStrategy.MAX)
        >>> node_results = [
        ...     AnomalyResult(..., metric_name="cpu_usage", anomaly_score=0.8),
        ...     AnomalyResult(..., metric_name="memory_used", anomaly_score=0.3),
        ... ]
        >>> agg_score = aggregator.aggregate(node_results)
        >>> print(f"Node is {agg_score.aggregate_score} anomalous")
    """
    
    def __init__(
        self,
        strategy: AggregationStrategy = AggregationStrategy.MAX,
        metric_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize node aggregator.
        
        Args:
            strategy: How to combine metric scores
            metric_weights: For WEIGHTED strategy, importance of each metric.
                           Example: {"cpu_usage": 0.5, "memory_used": 0.5}
                           If None, use uniform weights.
        """
        self.strategy = strategy
        self.metric_weights = metric_weights or {}
    
    def aggregate(
        self,
        anomaly_results: List[AnomalyResult],
        timestamp: Optional[datetime] = None,
    ) -> AggregatedAnomalyScore:
        """
        Aggregate anomaly scores for a node.
        
        Args:
            anomaly_results: List of AnomalyResults, all for same node
            timestamp: When aggregation was computed (default: now)
        
        Returns:
            AggregatedAnomalyScore combining all metrics
            
        Raises:
            ValueError: If list is empty or contains results from different nodes
        """
        if not anomaly_results:
            raise ValueError("Cannot aggregate empty result list")
        
        # Verify all results are for the same node
        first = anomaly_results[0]
        if not all(
            r.tenant_id == first.tenant_id and
            r.cluster_id == first.cluster_id and
            r.node_id == first.node_id
            for r in anomaly_results
        ):
            raise ValueError("All results must be from the same node")
        
        # Extract scores
        scores = [r.anomaly_score for r in anomaly_results]
        
        # Compute aggregated score based on strategy
        if self.strategy == AggregationStrategy.MAX:
            aggregate_score = max(scores)
        
        elif self.strategy == AggregationStrategy.MEAN:
            aggregate_score = sum(scores) / len(scores)
        
        elif self.strategy == AggregationStrategy.WEIGHTED:
            aggregate_score = self._weighted_mean(
                anomaly_results,
                scores,
            )
        
        elif self.strategy == AggregationStrategy.P95:
            aggregate_score = self._percentile(scores, 95)
        
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Count anomalies
        num_anomalies = sum(1 for r in anomaly_results if r.is_anomaly)
        
        return AggregatedAnomalyScore(
            tenant_id=first.tenant_id,
            cluster_id=first.cluster_id,
            node_id=first.node_id,
            aggregation_strategy=self.strategy.value,
            aggregate_score=aggregate_score,
            num_metrics_analyzed=len(anomaly_results),
            num_anomalies_detected=num_anomalies,
            timestamp=timestamp or datetime.utcnow(),
        )
    
    def _weighted_mean(
        self,
        anomaly_results: List[AnomalyResult],
        scores: List[float],
    ) -> float:
        """Compute weighted mean of scores"""
        total_weight = 0.0
        weighted_sum = 0.0
        
        for result, score in zip(anomaly_results, scores):
            # Get weight for this metric (default to 1.0)
            weight = self.metric_weights.get(result.metric_name, 1.0)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def _percentile(values: List[float], p: int) -> float:
        """Compute p-th percentile"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = (p / 100.0) * (len(sorted_vals) - 1)
        lower_idx = int(idx)
        upper_idx = lower_idx + 1
        
        if upper_idx >= len(sorted_vals):
            return sorted_vals[lower_idx]
        
        # Linear interpolation
        lower = sorted_vals[lower_idx]
        upper = sorted_vals[upper_idx]
        fraction = idx - lower_idx
        return lower + (upper - lower) * fraction


class ClusterAnomalyAggregator:
    """
    Aggregates node-level anomaly scores to cluster level.
    
    Input: List of node-level AggregatedAnomalyScore objects
    Output: Single cluster-level AggregatedAnomalyScore
    
    Ranking Feature:
        Returns nodes sorted by anomaly score (descending) for dashboard ranking.
    
    Example Usage:
        >>> aggregator = ClusterAnomalyAggregator(strategy=AggregationStrategy.MAX)
        >>> cluster_agg = aggregator.aggregate(node_scores)
        >>> top_nodes = aggregator.rank_nodes(node_scores, top_n=10)
    """
    
    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.MAX):
        """
        Initialize cluster aggregator.
        
        Args:
            strategy: How to combine node scores for cluster health
        """
        self.strategy = strategy
    
    def aggregate(
        self,
        node_scores: List[AggregatedAnomalyScore],
        timestamp: Optional[datetime] = None,
    ) -> AggregatedAnomalyScore:
        """
        Aggregate node scores to cluster level.
        
        Args:
            node_scores: List of node AggregatedAnomalyScore objects
            timestamp: When computed (default: now)
        
        Returns:
            Cluster-level AggregatedAnomalyScore (node_id=None)
        """
        if not node_scores:
            raise ValueError("Cannot aggregate empty node list")
        
        first = node_scores[0]
        if not all(
            n.tenant_id == first.tenant_id and
            n.cluster_id == first.cluster_id
            for n in node_scores
        ):
            raise ValueError("All nodes must be from same cluster")
        
        scores = [n.aggregate_score for n in node_scores]
        
        if self.strategy == AggregationStrategy.MAX:
            aggregate_score = max(scores)
        elif self.strategy == AggregationStrategy.MEAN:
            aggregate_score = sum(scores) / len(scores)
        elif self.strategy == AggregationStrategy.P95:
            aggregate_score = self._percentile(scores, 95)
        else:
            aggregate_score = max(scores)
        
        total_anomalies = sum(n.num_anomalies_detected for n in node_scores)
        
        return AggregatedAnomalyScore(
            tenant_id=first.tenant_id,
            cluster_id=first.cluster_id,
            node_id=None,  # Cluster level has no specific node
            aggregation_strategy=self.strategy.value,
            aggregate_score=aggregate_score,
            num_metrics_analyzed=len(node_scores),
            num_anomalies_detected=total_anomalies,
            timestamp=timestamp or datetime.utcnow(),
        )
    
    def rank_nodes(
        self,
        node_scores: List[AggregatedAnomalyScore],
        top_n: Optional[int] = None,
    ) -> List[AggregatedAnomalyScore]:
        """
        Rank nodes within cluster by anomaly severity.
        
        Args:
            node_scores: List of node AggregatedAnomalyScore objects
            top_n: Return only top N nodes (None = all)
        
        Returns:
            Nodes sorted by aggregate_score (descending)
        """
        ranked = sorted(
            node_scores,
            key=lambda x: x.aggregate_score,
            reverse=True,
        )
        return ranked[:top_n] if top_n else ranked
    
    @staticmethod
    def _percentile(values: List[float], p: int) -> float:
        """Compute p-th percentile"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = (p / 100.0) * (len(sorted_vals) - 1)
        lower_idx = int(idx)
        upper_idx = lower_idx + 1
        
        if upper_idx >= len(sorted_vals):
            return sorted_vals[lower_idx]
        
        lower = sorted_vals[lower_idx]
        upper = sorted_vals[upper_idx]
        fraction = idx - lower_idx
        return lower + (upper - lower) * fraction


class TenantAnomalyAggregator:
    """
    Aggregates cluster-level anomaly scores to tenant level.
    
    Enables multi-tenant SLA monitoring and health dashboards.
    """
    
    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.MAX):
        """Initialize tenant aggregator"""
        self.strategy = strategy
    
    def aggregate(
        self,
        cluster_scores: List[AggregatedAnomalyScore],
        timestamp: Optional[datetime] = None,
    ) -> AggregatedAnomalyScore:
        """
        Aggregate cluster scores to tenant level.
        
        Args:
            cluster_scores: List of cluster AggregatedAnomalyScore objects
            timestamp: When computed (default: now)
        
        Returns:
            Tenant-level AggregatedAnomalyScore (cluster_id=None, node_id=None)
        """
        if not cluster_scores:
            raise ValueError("Cannot aggregate empty cluster list")
        
        first = cluster_scores[0]
        if not all(c.tenant_id == first.tenant_id for c in cluster_scores):
            raise ValueError("All clusters must be from same tenant")
        
        scores = [c.aggregate_score for c in cluster_scores]
        
        if self.strategy == AggregationStrategy.MAX:
            aggregate_score = max(scores)
        elif self.strategy == AggregationStrategy.MEAN:
            aggregate_score = sum(scores) / len(scores)
        elif self.strategy == AggregationStrategy.P95:
            aggregate_score = self._percentile(scores, 95)
        else:
            aggregate_score = max(scores)
        
        total_anomalies = sum(c.num_anomalies_detected for c in cluster_scores)
        
        return AggregatedAnomalyScore(
            tenant_id=first.tenant_id,
            cluster_id=None,  # Tenant level
            node_id=None,
            aggregation_strategy=self.strategy.value,
            aggregate_score=aggregate_score,
            num_metrics_analyzed=len(cluster_scores),
            num_anomalies_detected=total_anomalies,
            timestamp=timestamp or datetime.utcnow(),
        )
    
    @staticmethod
    def _percentile(values: List[float], p: int) -> float:
        """Compute p-th percentile"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = (p / 100.0) * (len(sorted_vals) - 1)
        lower_idx = int(idx)
        upper_idx = lower_idx + 1
        
        if upper_idx >= len(sorted_vals):
            return sorted_vals[lower_idx]
        
        lower = sorted_vals[lower_idx]
        upper = sorted_vals[upper_idx]
        fraction = idx - lower_idx
        return lower + (upper - lower) * fraction


@dataclass
class AggregationConfig:
    """
    Configuration for multi-level aggregation pipeline.
    
    Example:
        >>> config = AggregationConfig(
        ...     node_strategy=AggregationStrategy.MAX,
        ...     cluster_strategy=AggregationStrategy.MEAN,
        ...     tenant_strategy=AggregationStrategy.MAX,
        ... )
        >>> pipeline = AggregationPipeline(config)
    """
    node_strategy: AggregationStrategy = AggregationStrategy.MAX
    cluster_strategy: AggregationStrategy = AggregationStrategy.MAX
    tenant_strategy: AggregationStrategy = AggregationStrategy.MAX
    metric_weights: Dict[str, float] = field(default_factory=dict)


class AggregationPipeline:
    """
    End-to-end aggregation from raw anomaly results to tenant scores.
    
    Orchestrates:
      1. Per-metric anomalies → node scores
      2. Node scores → cluster scores
      3. Cluster scores → tenant scores
    
    Example Usage:
        >>> pipeline = AggregationPipeline(config)
        >>> node_scores = pipeline.aggregate_nodes(anomaly_results)
        >>> cluster_scores = pipeline.aggregate_clusters(node_scores)
        >>> tenant_scores = pipeline.aggregate_tenants(cluster_scores)
    """
    
    def __init__(self, config: Optional[AggregationConfig] = None):
        """Initialize with configuration"""
        self.config = config or AggregationConfig()
        
        self.node_agg = NodeAnomalyAggregator(
            strategy=self.config.node_strategy,
            metric_weights=self.config.metric_weights,
        )
        self.cluster_agg = ClusterAnomalyAggregator(
            strategy=self.config.cluster_strategy,
        )
        self.tenant_agg = TenantAnomalyAggregator(
            strategy=self.config.tenant_strategy,
        )
    
    def aggregate_nodes(
        self,
        anomaly_results: List[AnomalyResult],
    ) -> Dict[str, List[AggregatedAnomalyScore]]:
        """
        Aggregate all anomaly results to per-node level.
        
        Returns:
            Dict mapping (tenant_id, cluster_id, node_id) → [AggregatedAnomalyScore]
        """
        # Group results by node
        by_node: Dict[tuple, List[AnomalyResult]] = {}
        for result in anomaly_results:
            key = (result.tenant_id, result.cluster_id, result.node_id)
            if key not in by_node:
                by_node[key] = []
            by_node[key].append(result)
        
        # Aggregate each node
        node_scores = {}
        for key, results in by_node.items():
            agg = self.node_agg.aggregate(results)
            node_scores[key] = agg
        
        return node_scores
