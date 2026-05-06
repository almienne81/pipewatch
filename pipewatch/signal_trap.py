"""Signal trapping utilities for graceful pipeline shutdown."""
from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Callable, List, Optional


class SignalTrapError(Exception):
    """Raised when signal trap configuration is invalid."""


@dataclass
class SignalTrap:
    """Registers handlers for OS signals and tracks whether a stop was requested."""

    signals: List[int] = field(default_factory=lambda: [signal.SIGINT, signal.SIGTERM])
    _triggered: Optional[int] = field(default=None, init=False, repr=False)
    _original: dict = field(default_factory=dict, init=False, repr=False)
    _callbacks: List[Callable[[int], None]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.signals:
            raise SignalTrapError("signals list must not be empty")

    def add_callback(self, fn: Callable[[int], None]) -> None:
        """Register a callback invoked with the signal number when triggered."""
        self._callbacks.append(fn)

    def arm(self) -> "SignalTrap":
        """Install handlers for all configured signals."""
        for sig in self.signals:
            self._original[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle)
        return self

    def disarm(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original.items():
            signal.signal(sig, handler)
        self._original.clear()

    def _handle(self, signum: int, _frame: object) -> None:
        self._triggered = signum
        for cb in self._callbacks:
            try:
                cb(signum)
            except Exception:  # noqa: BLE001
                pass

    @property
    def triggered(self) -> bool:
        """True if any registered signal has been received."""
        return self._triggered is not None

    @property
    def signal_received(self) -> Optional[int]:
        """The signal number that triggered the trap, or None."""
        return self._triggered

    def reset(self) -> None:
        """Clear the triggered state without restoring handlers."""
        self._triggered = None

    def __enter__(self) -> "SignalTrap":
        return self.arm()

    def __exit__(self, *_: object) -> None:
        self.disarm()

    def to_dict(self) -> dict:
        return {
            "signals": self.signals,
            "triggered": self.triggered,
            "signal_received": self._triggered,
        }
