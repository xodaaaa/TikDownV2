from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ActivityEvent:
    def __init__(self, type: str, payload: dict[str, Any]):
        self.type = type
        self.payload = payload


class BaseNotifier(ABC):
    @abstractmethod
    async def send(self, event: ActivityEvent) -> None: ...


_notifier_registry: dict[str, type[BaseNotifier]] = {}


def register_notifier(name: str, cls: type[BaseNotifier]) -> None:
    _notifier_registry[name] = cls


def get_notifier(name: str) -> type[BaseNotifier] | None:
    return _notifier_registry.get(name)


def list_notifiers() -> list[str]:
    return list(_notifier_registry.keys())
