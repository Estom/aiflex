"""Observability module for monitoring and tracing.

This module provides:
- Metrics collection (Prometheus)
- Distributed tracing (OpenTelemetry)
- Event bus system
"""

from .events import EventBus, EventHandler
from .metrics import MetricsCollector
from .tracing import Tracer

__all__ = [
    "EventBus",
    "EventHandler",
    "MetricsCollector",
    "Tracer",
]


class Event:
    """Event base class."""

    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data
        self.timestamp = None  # Set when emitted

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
        }
