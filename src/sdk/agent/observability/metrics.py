"""Metrics collector for Prometheus-style metrics."""

from typing import Dict
from time import time


class MetricsCollector:
    """
    Metrics collector for tracking Agent performance.

    Collects:
    - Agent execution time
    - Tool call counts and failures
    - Token consumption
    - Memory compression frequency
    """

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._enabled = True

    def counter(self, name: str, value: int = 1, labels: Dict[str, str] | None = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to add (default: 1)
            labels: Optional labels for the metric
        """
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """
        Record a histogram metric.

        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels for the metric
        """
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []

        self._histograms[key].append(value)

    def get_counter(self, name: str, labels: Dict[str, str] | None = None) -> int:
        """
        Get counter value.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            int: Counter value
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Dict[str, str] | None = None) -> float:
        """
        Get gauge value.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            float: Gauge value
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(self, name: str, labels: Dict[str, str] | None = None) -> Dict[str, float]:
        """
        Get histogram statistics.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            dict: Statistics (count, min, max, avg, sum)
        """
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._enabled

    def get_all_metrics(self) -> Dict[str, Dict]:
        """
        Get all metrics in Prometheus format.

        Returns:
            dict: All metrics organized by type
        """
        return {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": {k: self.get_histogram_stats(None, k) for k in self._histograms},
        }

    def _make_key(self, name: str, labels: Dict[str, str] | None = None) -> str:
        """
        Create a metric key with labels.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            str: Formatted key
        """
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
            return f"{name}{{{label_str}}}"
        return name


class Timer:
    """
    Context manager for timing operations.

    Usage:
        with Timer(metrics, "operation_name") as timer:
            # do something
        pass
    # timer automatically records duration
    """

    def __init__(self, metrics: MetricsCollector, name: str, labels: Dict[str, str] | None = None):
        self._metrics = metrics
        self._name = name
        self._labels = labels
        self._start_time = None
        self._end_time = None

    def __enter__(self):
        self._start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = time()
        duration = self._end_time - self._start_time

        if self._metrics.is_enabled():
            self._metrics.histogram(f"{self._name}_duration_seconds", duration, self._labels)

        return False
