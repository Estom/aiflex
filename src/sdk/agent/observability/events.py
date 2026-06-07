"""Event bus for system-wide event notification."""

from typing import Callable, Dict, List
from datetime import datetime


EventHandler = Callable[[dict], None]


class EventBus:
    """
    Event bus for managing event subscriptions and emissions.

    Supports:
    - Event subscription
    - Event emission
    - Event filtering by type
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_log: List[dict] = []
        self._enabled = True

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to
            handler: Handler function to call when event is emitted
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove

        Returns:
            bool: True if handler was removed, False if not found
        """
        if event_type not in self._handlers:
            return False

        try:
            self._handlers[event_type].remove(handler)
            return True
        except ValueError:
            return False

    def emit(self, event_type: str, data: dict) -> None:
        """
        Emit an event to all subscribers.

        Args:
            event_type: Event type
            data: Event data
        """
        if not self._enabled:
            return

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log event
        self._event_log.append(event)

        # Notify all subscribers
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't fail
                    pass

    def enable(self) -> None:
        """Enable event emission."""
        self._enabled = True

    def disable(self) -> None:
        """Disable event emission."""
        self._enabled = False

    def clear_handlers(self, event_type: str | None = None) -> None:
        """
        Clear event handlers.

        Args:
            event_type: Event type to clear, or None to clear all
        """
        if event_type is None:
            self._handlers.clear()
        elif event_type in self._handlers:
            self._handlers[event_type].clear()

    def get_event_log(self, limit: int | None = None) -> List[dict]:
        """
        Get event history log.

        Args:
            limit: Maximum number of events to return, or None for all

        Returns:
            List of event dictionaries
        """
        if limit is None:
            return self._event_log
        return self._event_log[-limit:]
