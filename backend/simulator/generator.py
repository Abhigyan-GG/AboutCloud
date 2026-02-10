"""
Metric Generator - Create synthetic cloud metrics

Generates realistic time-series data with configurable patterns and anomalies.
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import analytics types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.types import MetricSeries


@dataclass
class SimulatorConfig:
    """Configuration for metric simulation"""
    baseline_mean: float = 50.0
    baseline_std: float = 5.0
    sampling_interval_seconds: int = 60  # 1 minute
    noise_level: float = 0.1
    
    # Anomaly injection
    inject_spikes: bool = False
    inject_trends: bool = False
    inject_seasonal: bool = False
    
    spike_probability: float = 0.01
    spike_magnitude: float = 3.0  # Multiplier


class MetricSimulator:
    """
    Generate synthetic cloud metrics for testing.
    
    Usage:
        >>> sim = MetricSimulator()
        >>> series = sim.generate(
        ...     tenant_id="test-tenant",
        ...     cluster_id="test-cluster",
        ...     node_id="node-001",
        ...     metric_name="cpu_usage",
        ...     num_points=1000,
        ... )
    """
    
    def __init__(self, config: Optional[SimulatorConfig] = None):
        """Initialize simulator with configuration"""
        self.config = config or SimulatorConfig()
        random.seed(42)  # Reproducible for testing
        np.random.seed(42)
    
    def generate(
        self,
        tenant_id: str,
        cluster_id: str,
        node_id: str,
        metric_name: str,
        num_points: int = 1000,
        start_time: Optional[datetime] = None,
    ) -> MetricSeries:
        """
        Generate a metric time series.
        
        Args:
            tenant_id: Tenant identifier
            cluster_id: Cluster identifier
            node_id: Node identifier
            metric_name: Metric name (cpu_usage, memory_used, etc.)
            num_points: Number of data points to generate
            start_time: Starting timestamp (default: now)
        
        Returns:
            MetricSeries with generated data
        """
        if start_time is None:
            start_time = datetime.now()
        
        # Generate timestamps
        timestamps = [
            start_time + timedelta(seconds=i * self.config.sampling_interval_seconds)
            for i in range(num_points)
        ]
        
        # Generate baseline values
        values = self._generate_baseline(num_points)
        
        # Inject anomalies if configured
        if self.config.inject_spikes:
            values = self._inject_spikes(values)
        
        if self.config.inject_trends:
            values = self._inject_trend(values)
        
        if self.config.inject_seasonal:
            values = self._add_seasonality(values)
        
        # Add noise
        values = self._add_noise(values)
        
        # Clip to valid range (e.g., 0-100 for percentages)
        if "usage" in metric_name or "percent" in metric_name:
            values = np.clip(values, 0, 100)
        else:
            values = np.clip(values, 0, None)  # Non-negative
        
        return MetricSeries(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_id=node_id,
            metric_name=metric_name,
            timestamps=timestamps,
            values=values.tolist(),
            metadata={
                "source": "simulator",
                "config": str(self.config),
            }
        )
    
    def _generate_baseline(self, num_points: int) -> np.ndarray:
        """Generate baseline normal values"""
        return np.random.normal(
            self.config.baseline_mean,
            self.config.baseline_std,
            num_points
        )
    
    def _inject_spikes(self, values: np.ndarray) -> np.ndarray:
        """Inject random spikes into the data"""
        for i in range(len(values)):
            if random.random() < self.config.spike_probability:
                # Spike lasts 1-3 points
                spike_duration = random.randint(1, 3)
                for j in range(i, min(i + spike_duration, len(values))):
                    values[j] *= self.config.spike_magnitude
        return values
    
    def _inject_trend(self, values: np.ndarray, start_idx: Optional[int] = None) -> np.ndarray:
        """Inject an upward or downward trend"""
        if start_idx is None:
            start_idx = len(values) // 2  # Trend starts at midpoint
        
        trend_slope = random.choice([0.05, -0.05])  # Up or down
        for i in range(start_idx, len(values)):
            values[i] += trend_slope * (i - start_idx)
        
        return values
    
    def _add_seasonality(self, values: np.ndarray) -> np.ndarray:
        """Add seasonal (cyclic) pattern"""
        period = 100  # 100-point cycle
        amplitude = self.config.baseline_std * 2
        
        for i in range(len(values)):
            seasonal_component = amplitude * np.sin(2 * np.pi * i / period)
            values[i] += seasonal_component
        
        return values
    
    def _add_noise(self, values: np.ndarray) -> np.ndarray:
        """Add random noise"""
        noise = np.random.normal(0, self.config.noise_level, len(values))
        return values + noise


class AnomalyInjector:
    """
    Inject specific anomalies into existing time series.
    
    Use this to create labeled test data for ML evaluation.
    """
    
    @staticmethod
    def inject_spike(
        series: MetricSeries,
        spike_index: int,
        magnitude: float = 3.0,
        duration: int = 3,
    ) -> Tuple[MetricSeries, Dict]:
        """
        Inject a spike anomaly at a specific index.
        
        Returns:
            (modified_series, anomaly_metadata)
        """
        values = series.values.copy()
        original_value = values[spike_index]
        
        for i in range(spike_index, min(spike_index + duration, len(values))):
            values[i] *= magnitude
        
        modified_series = MetricSeries(
            tenant_id=series.tenant_id,
            cluster_id=series.cluster_id,
            node_id=series.node_id,
            metric_name=series.metric_name,
            timestamps=series.timestamps,
            values=values,
            metadata={**series.metadata, "anomaly_injected": "spike"}
        )
        
        metadata = {
            "type": "spike",
            "index": spike_index,
            "magnitude": magnitude,
            "duration": duration,
            "original_value": original_value,
            "anomalous_value": values[spike_index],
        }
        
        return modified_series, metadata
    
    @staticmethod
    def inject_trend(
        series: MetricSeries,
        start_index: int,
        slope: float = 0.1,
    ) -> Tuple[MetricSeries, Dict]:
        """
        Inject a trend anomaly starting at a specific index.
        
        Returns:
            (modified_series, anomaly_metadata)
        """
        values = series.values.copy()
        
        for i in range(start_index, len(values)):
            values[i] += slope * (i - start_index)
        
        modified_series = MetricSeries(
            tenant_id=series.tenant_id,
            cluster_id=series.cluster_id,
            node_id=series.node_id,
            metric_name=series.metric_name,
            timestamps=series.timestamps,
            values=values,
            metadata={**series.metadata, "anomaly_injected": "trend"}
        )
        
        metadata = {
            "type": "trend",
            "start_index": start_index,
            "slope": slope,
            "direction": "upward" if slope > 0 else "downward",
        }
        
        return modified_series, metadata
    
    @staticmethod
    def inject_level_shift(
        series: MetricSeries,
        shift_index: int,
        shift_amount: float = 20.0,
    ) -> Tuple[MetricSeries, Dict]:
        """
        Inject a sudden level shift (step function).
        
        Returns:
            (modified_series, anomaly_metadata)
        """
        values = series.values.copy()
        
        for i in range(shift_index, len(values)):
            values[i] += shift_amount
        
        modified_series = MetricSeries(
            tenant_id=series.tenant_id,
            cluster_id=series.cluster_id,
            node_id=series.node_id,
            metric_name=series.metric_name,
            timestamps=series.timestamps,
            values=values,
            metadata={**series.metadata, "anomaly_injected": "level_shift"}
        )
        
        metadata = {
            "type": "level_shift",
            "shift_index": shift_index,
            "shift_amount": shift_amount,
        }
        
        return modified_series, metadata


def generate_multi_node_scenario(
    tenant_id: str,
    cluster_id: str,
    num_nodes: int = 10,
    num_points: int = 1000,
    anomaly_node_ratio: float = 0.2,
) -> List[MetricSeries]:
    """
    Generate a multi-node scenario with some anomalous nodes.
    
    Args:
        tenant_id: Tenant ID
        cluster_id: Cluster ID
        num_nodes: Number of nodes to simulate
        num_points: Points per metric series
        anomaly_node_ratio: Fraction of nodes with anomalies
    
    Returns:
        List of MetricSeries, some with anomalies
    """
    simulator = MetricSimulator()
    series_list = []
    num_anomalous = int(num_nodes * anomaly_node_ratio)
    
    for i in range(num_nodes):
        node_id = f"node-{i:03d}"
        
        # Determine if this node should have anomalies
        has_anomaly = i < num_anomalous
        
        if has_anomaly:
            config = SimulatorConfig(
                inject_spikes=random.choice([True, False]),
                inject_trends=random.choice([True, False]),
            )
            simulator.config = config
        else:
            simulator.config = SimulatorConfig()  # Normal
        
        # Generate CPU usage metric
        series = simulator.generate(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            node_id=node_id,
            metric_name="cpu_usage",
            num_points=num_points,
        )
        
        series_list.append(series)
    
    return series_list


def _demo() -> None:
    """Run a quick demo when executing this file directly."""
    print("Metric Simulator Demo")
    print("=" * 60)

    config = SimulatorConfig(
        baseline_mean=60.0,
        baseline_std=8.0,
        inject_spikes=True,
        spike_probability=0.02,
        spike_magnitude=3.5,
    )
    sim = MetricSimulator(config)

    series = sim.generate(
        tenant_id="demo-tenant",
        cluster_id="demo-cluster",
        node_id="node-001",
        metric_name="cpu_usage",
        num_points=200,
    )

    print("Generated series:")
    print(f"  tenant:  {series.tenant_id}")
    print(f"  cluster: {series.cluster_id}")
    print(f"  node:    {series.node_id}")
    print(f"  metric:  {series.metric_name}")
    print(f"  points:  {len(series.values)}")
    print(f"  min:     {min(series.values):.2f}")
    print(f"  max:     {max(series.values):.2f}")
    print(f"  mean:    {sum(series.values) / len(series.values):.2f}")

    spiked, spike_meta = AnomalyInjector.inject_spike(
        series,
        spike_index=100,
        magnitude=4.0,
        duration=3,
    )
    print("\nInjected spike anomaly:")
    print(f"  index:      {spike_meta['index']}")
    print(f"  magnitude:  {spike_meta['magnitude']}x")
    print(f"  before:     {spike_meta['original_value']:.2f}")
    print(f"  after:      {spike_meta['anomalous_value']:.2f}")


if __name__ == "__main__":
    _demo()
