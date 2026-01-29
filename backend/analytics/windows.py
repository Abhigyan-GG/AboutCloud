"""
Sliding Window Extraction Logic

Implements deterministic window slicing over time series data.
This is the foundation for:
  - Feeding data to anomaly detection engines
  - Creating training/test splits
  - Batch processing of large time series

Design Principle:
  - Window size and stride are configurable
  - Windows are deterministic (same input → same windows)
  - Handles edge cases (partial windows, irregular sampling)
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .types import MetricSeries


@dataclass
class TimeWindow:
    """
    Represents a slice of a time series for analysis.
    
    Attributes:
        start_idx: Starting index in the original series (inclusive)
        end_idx: Ending index in the original series (exclusive)
        start_time: Timestamp of first point in window
        end_time: Timestamp of last point in window
        window_number: Sequential number (for tracking)
    """
    start_idx: int
    end_idx: int
    start_time: datetime
    end_time: datetime
    window_number: int
    
    @property
    def size(self) -> int:
        """Number of points in this window"""
        return self.end_idx - self.start_idx
    
    def __repr__(self) -> str:
        return (
            f"TimeWindow(#{self.window_number}, "
            f"points={self.size}, "
            f"{self.start_time} → {self.end_time})"
        )


class SlidingWindowExtractor:
    """
    Extracts sliding windows from time series data.
    
    Core Concept:
        Given a MetricSeries, create overlapping windows for batch analysis.
        Each window represents a time interval for anomaly detection.
    
    Example Usage:
        >>> extractor = SlidingWindowExtractor(
        ...     window_size_points=100,
        ...     stride_points=50
        ... )
        >>> windows = extractor.extract(metric_series)
        >>> for window in windows:
        ...     print(f"Analyzing {window.size} points from "
        ...           f"{window.start_time} to {window.end_time}")
    """
    
    def __init__(
        self,
        window_size_points: int = 100,
        stride_points: Optional[int] = None,
        include_partial_windows: bool = False,
    ):
        """
        Initialize window extraction parameters.
        
        Args:
            window_size_points: Number of data points per window (default: 100)
            stride_points: Number of points to skip between windows.
                          If None, use window_size_points (non-overlapping).
            include_partial_windows: If True, include windows with fewer than
                                    window_size_points at the end of series.
                                    If False, discard incomplete final window.
        """
        if window_size_points <= 0:
            raise ValueError(f"window_size_points must be positive, got {window_size_points}")
        
        self.window_size_points = window_size_points
        self.stride_points = stride_points or window_size_points
        self.include_partial_windows = include_partial_windows
        
        if self.stride_points <= 0:
            raise ValueError(f"stride_points must be positive, got {self.stride_points}")
    
    def extract(self, time_series: MetricSeries) -> List[TimeWindow]:
        """
        Extract all windows from a time series.
        
        Deterministic algorithm:
          1. Start at index 0
          2. Create window from [i, i+window_size)
          3. Step forward by stride_points
          4. Repeat until end of series
        
        Args:
            time_series: MetricSeries to window
        
        Returns:
            List[TimeWindow]: All extracted windows, in order
            
        Raises:
            ValueError: If series is too short for even one window
        """
        series_length = len(time_series.timestamps)
        
        if series_length < self.window_size_points:
            if self.include_partial_windows and series_length > 0:
                # Create one partial window covering entire series
                return [
                    TimeWindow(
                        start_idx=0,
                        end_idx=series_length,
                        start_time=time_series.timestamps[0],
                        end_time=time_series.timestamps[-1],
                        window_number=1,
                    )
                ]
            else:
                raise ValueError(
                    f"Series has {series_length} points but window_size is "
                    f"{self.window_size_points}. Consider setting "
                    f"include_partial_windows=True"
                )
        
        windows: List[TimeWindow] = []
        window_num = 1
        
        # Generate windows with stride
        start_idx = 0
        while start_idx < series_length:
            end_idx = min(start_idx + self.window_size_points, series_length)
            
            # Check if window is complete or we allow partial windows
            if end_idx - start_idx == self.window_size_points or self.include_partial_windows:
                window = TimeWindow(
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_time=time_series.timestamps[start_idx],
                    end_time=time_series.timestamps[end_idx - 1],
                    window_number=window_num,
                )
                windows.append(window)
                window_num += 1
            
            start_idx += self.stride_points
        
        return windows
    
    def extract_window_data(
        self,
        time_series: MetricSeries,
        window: TimeWindow,
    ) -> Tuple[List[datetime], List[float]]:
        """
        Extract actual data for a specific window.
        
        Args:
            time_series: Original metric series
            window: TimeWindow object describing the slice
        
        Returns:
            (timestamps, values) for that window
        """
        timestamps = time_series.timestamps[window.start_idx:window.end_idx]
        values = time_series.values[window.start_idx:window.end_idx]
        return timestamps, values
    
    @property
    def config(self) -> dict:
        """Return configuration as dictionary (useful for logging/debugging)"""
        return {
            "window_size_points": self.window_size_points,
            "stride_points": self.stride_points,
            "include_partial_windows": self.include_partial_windows,
            "is_overlapping": self.stride_points < self.window_size_points,
        }


class TimeBasedWindowExtractor:
    """
    Alternative: Extract windows based on wall-clock time instead of point count.
    
    Useful for:
      - Hourly/daily aggregations
      - Irregular sampling rates
      - Calendar-based analysis
    
    Example:
        >>> extractor = TimeBasedWindowExtractor(
        ...     window_duration=timedelta(hours=1),
        ...     stride_duration=timedelta(minutes=30)
        ... )
        >>> windows = extractor.extract(metric_series)
    """
    
    def __init__(
        self,
        window_duration: timedelta,
        stride_duration: Optional[timedelta] = None,
        include_partial_windows: bool = False,
    ):
        """
        Initialize time-based window extraction.
        
        Args:
            window_duration: Duration of each window (e.g., 1 hour)
            stride_duration: Time to advance between windows.
                            If None, equals window_duration (non-overlapping).
            include_partial_windows: Include windows shorter than window_duration
        """
        self.window_duration = window_duration
        self.stride_duration = stride_duration or window_duration
        self.include_partial_windows = include_partial_windows
    
    def extract(self, time_series: MetricSeries) -> List[TimeWindow]:
        """Extract windows based on time boundaries"""
        if len(time_series.timestamps) == 0:
            return []
        
        windows: List[TimeWindow] = []
        window_num = 1
        
        current_start_time = time_series.timestamps[0]
        
        while current_start_time < time_series.timestamps[-1]:
            current_end_time = current_start_time + self.window_duration
            
            # Find indices in this time range
            start_idx = self._find_idx_ge(time_series.timestamps, current_start_time)
            end_idx = self._find_idx_lt(time_series.timestamps, current_end_time)
            
            if start_idx is not None and end_idx is not None and start_idx < end_idx:
                actual_start = time_series.timestamps[start_idx]
                actual_end = time_series.timestamps[end_idx - 1]
                
                window = TimeWindow(
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_time=actual_start,
                    end_time=actual_end,
                    window_number=window_num,
                )
                windows.append(window)
                window_num += 1
            
            current_start_time += self.stride_duration
        
        return windows
    
    @staticmethod
    def _find_idx_ge(timestamps: List[datetime], target: datetime) -> Optional[int]:
        """Find first index where timestamps[i] >= target"""
        for i, ts in enumerate(timestamps):
            if ts >= target:
                return i
        return None
    
    @staticmethod
    def _find_idx_lt(timestamps: List[datetime], target: datetime) -> Optional[int]:
        """Find first index where timestamps[i] >= target (exclusive range end)"""
        for i, ts in enumerate(timestamps):
            if ts >= target:
                return i
        return len(timestamps)  # All points are < target
