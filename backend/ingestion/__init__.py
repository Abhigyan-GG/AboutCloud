"""
Data Ingestion Layer

Handles metric collection, validation, and routing to storage.
"""

from .collector import MetricCollector
from .validator import MetricValidator
from .pipeline import IngestionPipeline

__all__ = [
    "MetricCollector",
    "MetricValidator",
    "IngestionPipeline",
]
