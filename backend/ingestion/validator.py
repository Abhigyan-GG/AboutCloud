"""
Metric Validator - Validate incoming metrics

Ensures data quality before ingestion into storage.
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.types import MetricSeries


@dataclass
class ValidationResult:
    """Result of metric validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        """Allow using as boolean"""
        return self.is_valid


class MetricValidator:
    """
    Validate metric data quality.
    
    Checks:
    - Required fields present
    - Timestamps in order
    - No missing/null values
    - Data within expected bounds
    - Multi-tenant isolation
    
    Usage:
        >>> validator = MetricValidator()
        >>> result = validator.validate(metric_series)
        >>> if result.is_valid:
        ...     # Proceed with ingestion
        ... else:
        ...     # Log errors
    """
    
    def __init__(
        self,
        allow_empty: bool = False,
        max_gap_seconds: int = 300,  # 5 minutes
        require_sorted: bool = True,
    ):
        """
        Initialize validator.
        
        Args:
            allow_empty: Allow empty time series (default: False)
            max_gap_seconds: Maximum allowed gap between consecutive points
            require_sorted: Require timestamps to be sorted (default: True)
        """
        self.allow_empty = allow_empty
        self.max_gap_seconds = max_gap_seconds
        self.require_sorted = require_sorted
    
    def validate(self, series: MetricSeries) -> ValidationResult:
        """
        Validate a metric series.
        
        Args:
            series: MetricSeries to validate
        
        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []
        
        # Check required fields
        if not series.tenant_id:
            errors.append("Missing tenant_id")
        
        if not series.cluster_id:
            errors.append("Missing cluster_id")
        
        if not series.node_id:
            errors.append("Missing node_id")
        
        if not series.metric_name:
            errors.append("Missing metric_name")
        
        # Check data presence
        if not series.timestamps or not series.values:
            if not self.allow_empty:
                errors.append("Empty time series (no data)")
        
        # Check length mismatch
        if len(series.timestamps) != len(series.values):
            errors.append(
                f"Length mismatch: {len(series.timestamps)} timestamps, "
                f"{len(series.values)} values"
            )
        
        # If no data, return early
        if not series.timestamps or not series.values:
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
            )
        
        # Check for null/NaN values
        if any(v is None or (isinstance(v, float) and v != v) for v in series.values):
            errors.append("Contains null or NaN values")
        
        # Check timestamps are sorted
        if self.require_sorted:
            if series.timestamps != sorted(series.timestamps):
                errors.append("Timestamps not in chronological order")
        
        # Check for duplicate timestamps
        if len(series.timestamps) != len(set(series.timestamps)):
            warnings.append("Contains duplicate timestamps")
        
        # Check for large gaps
        if len(series.timestamps) > 1:
            for i in range(1, len(series.timestamps)):
                gap = (series.timestamps[i] - series.timestamps[i-1]).total_seconds()
                if gap > self.max_gap_seconds:
                    warnings.append(
                        f"Large gap detected: {gap}s between "
                        f"{series.timestamps[i-1]} and {series.timestamps[i]}"
                    )
                if gap < 0:
                    errors.append("Timestamps not monotonically increasing")
        
        # Check value bounds (for percentage metrics)
        if "usage" in series.metric_name or "percent" in series.metric_name:
            if any(v < 0 or v > 100 for v in series.values if v is not None):
                warnings.append("Percentage metric contains values outside [0, 100]")
        
        # Check for negative values (for count/rate metrics)
        if "count" in series.metric_name or "rate" in series.metric_name:
            if any(v < 0 for v in series.values if v is not None):
                warnings.append("Count/rate metric contains negative values")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def validate_batch(
        self,
        series_list: List[MetricSeries],
    ) -> Tuple[List[MetricSeries], List[MetricSeries], List[str]]:
        """
        Validate a batch of metric series.
        
        Args:
            series_list: List of MetricSeries to validate
        
        Returns:
            Tuple of (valid_series, invalid_series, error_messages)
        """
        valid = []
        invalid = []
        all_errors = []
        
        for i, series in enumerate(series_list):
            result = self.validate(series)
            
            if result.is_valid:
                valid.append(series)
                # Log warnings but keep series
                if result.warnings:
                    all_errors.append(
                        f"Series {i} ({series.node_id}/{series.metric_name}): "
                        f"WARNINGS: {'; '.join(result.warnings)}"
                    )
            else:
                invalid.append(series)
                all_errors.append(
                    f"Series {i} ({series.node_id}/{series.metric_name}): "
                    f"ERRORS: {'; '.join(result.errors)}"
                )
        
        return valid, invalid, all_errors


class TenantIsolationValidator:
    """
    Validate multi-tenant isolation.
    
    Ensures that data from one tenant cannot leak to another tenant.
    """
    
    @staticmethod
    def validate_tenant_isolation(
        series_list: List[MetricSeries],
        expected_tenant_id: str,
    ) -> ValidationResult:
        """
        Validate that all series belong to the expected tenant.
        
        Args:
            series_list: List of MetricSeries
            expected_tenant_id: Expected tenant ID
        
        Returns:
            ValidationResult
        """
        errors = []
        
        for i, series in enumerate(series_list):
            if series.tenant_id != expected_tenant_id:
                errors.append(
                    f"Series {i}: tenant_id mismatch "
                    f"(expected: {expected_tenant_id}, got: {series.tenant_id})"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
        )
