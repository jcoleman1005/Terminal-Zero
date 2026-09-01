from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, callback: Callable[[Event], None], event_type: str = "*"):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event):
        for cb in self._subscribers.get(event.type, []):
            cb(event)
        for cb in self._subscribers.get("*", []):
            cb(event)
