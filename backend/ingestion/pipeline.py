"""
Ingestion Pipeline - Orchestrate metric collection, validation, and storage

Coordinates the flow: Collect → Validate → Store
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.types import MetricSeries
from backend.ingestion.collector import MetricCollector, MetricSource
from backend.ingestion.validator import MetricValidator, TenantIsolationValidator


@dataclass
class IngestionStats:
    """Statistics from ingestion run"""
    total_collected: int = 0
    total_valid: int = 0
    total_invalid: int = 0
    total_stored: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_collected == 0:
            return 0.0
        return self.total_valid / self.total_collected


class IngestionPipeline:
    """
    Orchestrate the full ingestion pipeline.
    
    Flow:
    1. Collect metrics from source
    2. Validate data quality
    3. Store to storage layer
    4. Return statistics
    
    Usage:
        >>> pipeline = IngestionPipeline(
        ...     collector=MetricCollector(SimulatorSource()),
        ...     validator=MetricValidator(),
        ...     storage=storage_backend,
        ... )
        >>> stats = pipeline.ingest_cluster(
        ...     tenant_id="test",
        ...     cluster_id="cluster-1",
        ...     node_ids=["node-001", "node-002"],
        ...     metric_name="cpu_usage",
        ...     start_time=datetime(2025, 1, 1),
        ...     end_time=datetime(2025, 1, 2),
        ... )
    """
    
    def __init__(
        self,
        collector: MetricCollector,
        validator: MetricValidator,
        storage: Optional[object] = None,  # StorageBackend interface (Phase 2)
    ):
        """
        Initialize pipeline.
        
        Args:
            collector: MetricCollector instance
            validator: MetricValidator instance
            storage: Storage backend (optional for now)
        """
        self.collector = collector
        self.validator = validator
        self.storage = storage
    
    def ingest_metric(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[MetricSeries, IngestionStats]:
        """
        Ingest a single metric.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            (MetricSeries, IngestionStats)
        """
        stats = IngestionStats()
        
        # 1. Collect
        series = self.collector.collect_metric(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_id=node_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
        )
        stats.total_collected = 1
        
        # 2. Validate
        validation = self.validator.validate(series)
        
        if not validation.is_valid:
            stats.total_invalid = 1
            stats.errors.extend(validation.errors)
            return None, stats
        
        stats.total_valid = 1
        
        # Log warnings
        if validation.warnings:
            stats.errors.extend([f"WARNING: {w}" for w in validation.warnings])
        
        # 3. Store (if storage configured)
        if self.storage:
            try:
                self.storage.store_metric(series)
                stats.total_stored = 1
            except Exception as e:
                stats.errors.append(f"Storage error: {str(e)}")
                stats.total_stored = 0
        
        return series, stats
    
    def ingest_cluster(
        self,
        tenant_id: str,
        cluster_id: str,
        node_ids: List[str],
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[List[MetricSeries], IngestionStats]:
        """
        Ingest metrics for all nodes in a cluster.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_ids: List of node identifiers
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            (List of valid MetricSeries, IngestionStats)
        """
        stats = IngestionStats()
        
        # 1. Collect all metrics
        series_list = self.collector.collect_cluster_metrics(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_ids=node_ids,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
        )
        stats.total_collected = len(series_list)
        
        # 2. Validate tenant isolation
        isolation_result = TenantIsolationValidator.validate_tenant_isolation(
            series_list, tenant_id
        )
        
        if not isolation_result.is_valid:
            stats.errors.extend(isolation_result.errors)
            # This is a critical error - tenant isolation violated
            return [], stats
        
        # 3. Validate each series
        valid_series, invalid_series, error_msgs = self.validator.validate_batch(
            series_list
        )
        
        stats.total_valid = len(valid_series)
        stats.total_invalid = len(invalid_series)
        stats.errors.extend(error_msgs)
        
        # 4. Store valid series (if storage configured)
        if self.storage and valid_series:
            try:
                for series in valid_series:
                    self.storage.store_metric(series)
                stats.total_stored = len(valid_series)
            except Exception as e:
                stats.errors.append(f"Storage error: {str(e)}")
                stats.total_stored = 0
        
        return valid_series, stats
    
    def get_stats_summary(self, stats: IngestionStats) -> str:
        """
        Get a human-readable summary of ingestion stats.
        
        Args:
            stats: IngestionStats
        
        Returns:
            Formatted summary string
        """
        summary = [
            "Ingestion Statistics:",
            f"  Collected: {stats.total_collected}",
            f"  Valid:     {stats.total_valid}",
            f"  Invalid:   {stats.total_invalid}",
            f"  Stored:    {stats.total_stored}",
            f"  Success:   {stats.success_rate():.1%}",
        ]
        
        if stats.errors:
            summary.append(f"\nErrors/Warnings ({len(stats.errors)}):")
            for err in stats.errors[:5]:  # Show first 5
                summary.append(f"  - {err}")
            if len(stats.errors) > 5:
                summary.append(f"  ... and {len(stats.errors) - 5} more")
        
        return "\n".join(summary)
