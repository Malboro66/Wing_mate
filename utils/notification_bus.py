from __future__ import annotations

from enum import Enum
from typing import Callable, List, Optional


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


try:
    from PyQt5.QtCore import QObject, pyqtSignal

    class NotificationBus(QObject):
        """Observer bus global para notificações thread-safe via sinal Qt."""

        _instance: Optional["NotificationBus"] = None
        notified = pyqtSignal(str, str, int)

        def notify(self, level: NotificationLevel, message: str, timeout_ms: int = 3000) -> None:
            self.notified.emit(level.value, str(message or ""), int(timeout_ms or 0))

        def send(self, level: NotificationLevel, message: str, timeout_ms: int = 3000) -> None:
            self.notify(level, message, timeout_ms)

        @classmethod
        def instance(cls) -> "NotificationBus":
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

except ModuleNotFoundError:

    class _FallbackSignal:
        def __init__(self) -> None:
            self._subs: List[Callable[[str, str, int], None]] = []

        def connect(self, fn: Callable[[str, str, int], None], *_args, **_kwargs) -> None:
            self._subs.append(fn)

        def emit(self, level: str, message: str, timeout_ms: int) -> None:
            for fn in list(self._subs):
                fn(level, message, timeout_ms)

    class NotificationBus:
        """Fallback sem Qt (usado em ambientes de teste sem PyQt)."""

        _instance: Optional["NotificationBus"] = None

        def __init__(self) -> None:
            self.notified = _FallbackSignal()

        def notify(self, level: NotificationLevel, message: str, timeout_ms: int = 3000) -> None:
            self.notified.emit(level.value, str(message or ""), int(timeout_ms or 0))

        def send(self, level: NotificationLevel, message: str, timeout_ms: int = 3000) -> None:
            self.notify(level, message, timeout_ms)

        @classmethod
        def instance(cls) -> "NotificationBus":
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance


notification_bus = NotificationBus.instance()


def notify_info(message: str, timeout_ms: int = 2500) -> None:
    NotificationBus.instance().send(NotificationLevel.INFO, message, timeout_ms)


def notify_warning(message: str, timeout_ms: int = 3500) -> None:
    NotificationBus.instance().send(NotificationLevel.WARNING, message, timeout_ms)


def notify_error(message: str, timeout_ms: int = 4500) -> None:
    NotificationBus.instance().send(NotificationLevel.ERROR, message, timeout_ms)
