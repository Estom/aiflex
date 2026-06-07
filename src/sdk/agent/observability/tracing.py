"""Distributed tracing using OpenTelemetry-style tracing."""

from typing import Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager


class Span:
    """
    A span represents a unit of work or operation.

    Spans can be:
    - Started
    - Finished
    - Have attributes
    - Have events
    - Have children (parent-child relationship)
    """

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = self._generate_span_id()
        self.parent_span_id = parent_span_id
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, any] = {}
        self.events: List[Dict] = []
        self.status: str = "ok"  # ok, error

    def start(self) -> None:
        """Start the span."""
        import time
        self.start_time = time.time()

    def finish(self) -> None:
        """Finish the span."""
        import time
        self.end_time = time.time()

    def set_attribute(self, key: str, value: any) -> None:
        """Set an attribute on the span."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Dict[str, any] | None = None) -> None:
        """Add an event to the span."""
        event = {
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if attributes:
            event["attributes"] = attributes
        self.events.append(event)

    def set_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Mark span as error."""
        self.status = "error"
        self.set_attribute("error.message", message)
        if exception:
            self.set_attribute("error.type", type(exception).__name__)
            self.set_attribute("error.stack", str(exception))

    def duration(self) -> float:
        """Get span duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def to_dict(self) -> Dict:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration(),
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }

    @staticmethod
    def _generate_span_id() -> str:
        """Generate unique span ID."""
        import uuid
        return str(uuid.uuid4())


class Tracer:
    """
    Tracer for creating and managing spans.

    Provides:
    - Span creation
    - Trace context management
    - Span storage and export
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._active_span: Optional[Span] = None
        self._span_stack: List[Span] = []
        self._spans: List[Span] = []
        self._enabled = True

    def start_span(self, name: str) -> Span:
        """
        Start a new span.

        Args:
            name: Span name

        Returns:
            Span: New span instance
        """
        trace_id = self._get_trace_id()
        parent_span_id = self._active_span.span_id if self._active_span else None

        span = Span(name, trace_id, parent_span_id)
        span.start()

        # Push to stack
        self._span_stack.append(span)
        self._active_span = span

        return span

    def finish_span(self, span: Span) -> None:
        """
        Finish a span.

        Args:
            span: Span to finish
        """
        span.finish()

        # Pop from stack if it's the active span
        if self._active_span == span:
            if self._span_stack:
                self._span_stack.pop()
            self._active_span = self._span_stack[-1] if self._span_stack else None

        # Store finished span
        self._spans.append(span)

    def active_span(self) -> Optional[Span]:
        """Get the currently active span."""
        return self._active_span

    @contextmanager
    def span(self, name: str):
        """
        Context manager for automatic span lifecycle.

        Usage:
            with tracer.span("operation_name") as span:
                # do work
                span.set_attribute("key", "value")
        """
        span = self.start_span(name)
        try:
            yield span
        finally:
            self.finish_span(span)

    def enable(self) -> None:
        """Enable tracing."""
        self._enabled = True

    def disable(self) -> None:
        """Disable tracing."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._enabled

    def clear_spans(self) -> None:
        """Clear all stored spans."""
        self._spans.clear()
        self._span_stack.clear()
        self._active_span = None

    def get_spans(self) -> List[Span]:
        """Get all stored spans."""
        return self._spans.copy()

    def get_trace_id(self) -> str:
        """Get current trace ID."""
        return self._get_trace_id()

    def _get_trace_id(self) -> str:
        """
        Get or generate trace ID.

        Returns the trace ID of the active span, or generates a new one.
        """
        if self._active_span:
            return self._active_span.trace_id

        import uuid
        return str(uuid.uuid4())

    def export_spans(self) -> List[Dict]:
        """
        Export all spans in JSON format.

        Returns:
            List of span dictionaries
        """
        return [span.to_dict() for span in self._spans]
