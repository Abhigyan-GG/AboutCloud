"""
Storage Interface - Abstract storage contract

This interface is what the analytics module expects (from INTEGRATION_CONTRACT.py).
"""

import sys
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.types import MetricSeries, AnomalyResult, AggregatedAnomalyScore


class StorageBackend(ABC):
    """
    Abstract storage backend.
    
    All storage implementations (in-memory, database, time-series DB, etc.)
    must implement this interface.
    """
    
    @abstractmethod
    def store_metric(self, series: MetricSeries) -> None:
        """
        Store a metric time series.
        
        Args:
            series: MetricSeries to store
        """
        pass
    
    @abstractmethod
    def get_metric_series(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> MetricSeries:
        """
        Retrieve a metric time series.
        
        This is the function signature expected by the analytics module.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            MetricSeries for the specified query
        
        Raises:
            ValueError: If no data found
        """
        pass
    
    @abstractmethod
    def store_anomaly_result(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        result: AnomalyResult,
    ) -> None:
        """
        Store anomaly detection results.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name
            result: AnomalyResult to store
        """
        pass
    
    @abstractmethod
    def store_aggregated_score(
        self,
        score: AggregatedAnomalyScore,
    ) -> None:
        """
        Store aggregated anomaly score.
        
        Args:
            score: AggregatedAnomalyScore to store
        """
        pass
    
    @abstractmethod
    def query_anomalies(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
        cluster_id: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[Dict]:
        """
        Query stored anomaly results.
        
        Args:
            tenant_id: Tenant identifier
            start_time: Start of time range
            end_time: End of time range
            cluster_id: Optional cluster filter
            min_score: Minimum anomaly score threshold
        
        Returns:
            List of anomaly records
        """
        pass


# Global storage instance (singleton pattern)
_storage_backend: Optional[StorageBackend] = None


def configure_storage(backend: StorageBackend) -> None:
    """
    Configure the global storage backend.
    
    Args:
        backend: StorageBackend implementation
    """
    global _storage_backend
    _storage_backend = backend


def get_storage() -> StorageBackend:
    """
    Get the configured storage backend.
    
    Returns:
        StorageBackend instance
    
    Raises:
        RuntimeError: If storage not configured
    """
    if _storage_backend is None:
        raise RuntimeError(
            "Storage backend not configured. "
            "Call configure_storage() first."
        )
    return _storage_backend


def get_metric_series(
    tenant_id: str,
    cluster_id: str,
    node_id: str,
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
) -> MetricSeries:
    """
    Convenience function to get metric series from configured storage.
    
    This matches the interface contract expected by the analytics module.
    
    Args:
        tenant_id: Tenant identifier
        cluster_id: Cluster identifier
        node_id: Node identifier
        metric_name: Metric name
        start_time: Start of time range
        end_time: End of time range
    
    Returns:
        MetricSeries from storage
    """
    backend = get_storage()
    return backend.get_metric_series(
        tenant_id=tenant_id,
        cluster_id=cluster_id,
        node_id=node_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
    )
