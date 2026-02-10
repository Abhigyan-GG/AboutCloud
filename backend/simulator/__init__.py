"""
Metric Simulator - Generate synthetic cloud performance metrics

This module generates realistic time-series data for testing the analytics pipeline.
Supports:
  - Normal baseline patterns
  - Injected anomalies (spikes, trends, seasonal deviations)
  - Multiple metric types (CPU, memory, disk, network)
  - Multi-tenant simulation
"""

from .generator import MetricSimulator, AnomalyInjector, SimulatorConfig, generate_multi_node_scenario

__all__ = [
    "MetricSimulator",
    "AnomalyInjector",
    "SimulatorConfig",
    "generate_multi_node_scenario",
]
