"""
Storage Layer - Persist and retrieve metrics

Implements the storage interface needed by analytics module.
"""

from .interface import StorageBackend, get_metric_series
from .memory_storage import InMemoryStorage

__all__ = [
    "StorageBackend",
    "get_metric_series",
    "InMemoryStorage",
]
