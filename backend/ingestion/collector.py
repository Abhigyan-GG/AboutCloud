"""
Metric Collector - Collect metrics from various sources

Supports:
- Simulator (for testing)
- Future: Prometheus, CloudWatch, Azure Monitor, etc.
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.types import MetricSeries


class MetricSource(Protocol):
    """Protocol for metric sources"""
    
    def collect(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> MetricSeries:
        """Collect metrics from source"""
        ...


class SimulatorSource:
    """
    Metric source using the simulator (for testing).
    
    Usage:
        >>> source = SimulatorSource()
        >>> series = source.collect(
        ...     tenant_id="test",
        ...     cluster_id="cluster-1",
        ...     node_id="node-001",
        ...     metric_name="cpu_usage",
        ...     start_time=datetime(2025, 1, 1),
        ...     end_time=datetime(2025, 1, 2),
        ... )
    """
    
    def __init__(self):
        """Initialize simulator source"""
        from backend.simulator.generator import MetricSimulator, SimulatorConfig
        self.simulator = MetricSimulator(SimulatorConfig())
    
    def collect(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> MetricSeries:
        """
        Collect simulated metrics.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            MetricSeries with simulated data
        """
        # Calculate number of points based on time range
        duration_seconds = (end_time - start_time).total_seconds()
        num_points = int(duration_seconds / self.simulator.config.sampling_interval_seconds)
        
        return self.simulator.generate(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_id=node_id,
            metric_name=metric_name,
            num_points=num_points,
            start_time=start_time,
        )


class MetricCollector:
    """
    High-level metric collector.
    
    Collects metrics from configured sources and prepares them for validation.
    
    Usage:
        >>> collector = MetricCollector(source=SimulatorSource())
        >>> series = collector.collect_metric(
        ...     tenant_id="test",
        ...     cluster_id="cluster-1",
        ...     node_id="node-001",
        ...     metric_name="cpu_usage",
        ...     start_time=datetime(2025, 1, 1),
        ...     end_time=datetime(2025, 1, 2),
        ... )
    """
    
    def __init__(self, source: MetricSource):
        """
        Initialize collector with a metric source.
        
        Args:
            source: Metric source (SimulatorSource, PrometheusSource, etc.)
        """
        self.source = source
    
    def collect_metric(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> MetricSeries:
        """
        Collect a single metric.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name (cpu_usage, memory_used, etc.)
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            MetricSeries collected from source
        """
        return self.source.collect(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_id=node_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
        )
    
    def collect_cluster_metrics(
        self,
        tenant_id: str,
        cluster_id: str,
        node_ids: List[str],
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[MetricSeries]:
        """
        Collect metrics for multiple nodes in a cluster.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_ids: List of node identifiers
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            List of MetricSeries (one per node)
        """
        series_list = []
        for node_id in node_ids:
            series = self.collect_metric(
                tenant_id=tenant_id,
                cluster_id=cluster_id,
                node_id=node_id,
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
            )
            series_list.append(series)
        return series_list


# Future: PrometheusSource, CloudWatchSource, etc.
# class PrometheusSource:
#     def __init__(self, prometheus_url: str):
#         self.url = prometheus_url
#     
#     def collect(self, ...):
#         # Query Prometheus API
#         ...
