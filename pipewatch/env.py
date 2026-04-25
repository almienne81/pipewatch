"""Environment snapshot utilities for capturing runtime context during pipeline runs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EnvError(Exception):
    """Raised when environment snapshot operations fail."""


@dataclass(frozen=True)
class EnvSnapshot:
    """Immutable snapshot of selected environment variables."""

    variables: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return the value for *key* or *default* if absent."""
        return self.variables.get(key, default)

    def keys(self) -> List[str]:
        """Return sorted list of captured variable names."""
        return sorted(self.variables.keys())

    def to_dict(self) -> Dict[str, str]:
        """Return a plain dict copy of the snapshot."""
        return dict(self.variables)

    def __len__(self) -> int:
        return len(self.variables)


def capture(keys: Optional[List[str]] = None, prefix: Optional[str] = None) -> EnvSnapshot:
    """Capture environment variables into an :class:`EnvSnapshot`.

    Args:
        keys: Explicit list of variable names to capture.  When *None* and
              *prefix* is also *None*, **all** current env vars are captured.
        prefix: If provided, capture every variable whose name starts with
                this string (case-sensitive).  Ignored when *keys* is given.

    Returns:
        A frozen :class:`EnvSnapshot` containing the selected variables.

    Raises:
        EnvError: If both *keys* and *prefix* are supplied simultaneously.
    """
    if keys is not None and prefix is not None:
        raise EnvError("Specify either 'keys' or 'prefix', not both.")

    env = os.environ

    if keys is not None:
        captured = {k: env[k] for k in keys if k in env}
    elif prefix is not None:
        captured = {k: v for k, v in env.items() if k.startswith(prefix)}
    else:
        captured = dict(env)

    return EnvSnapshot(variables=captured)


def diff(before: EnvSnapshot, after: EnvSnapshot) -> Dict[str, Dict[str, Optional[str]]]:
    """Return variables that changed between two snapshots.

    Returns a mapping of ``{key: {"before": ..., "after": ...}}`` for every
    key that was added, removed, or whose value changed.
    """
    all_keys = set(before.keys()) | set(after.keys())
    changes: Dict[str, Dict[str, Optional[str]]] = {}
    for key in all_keys:
        b = before.get(key)
        a = after.get(key)
        if b != a:
            changes[key] = {"before": b, "after": a}
    return changes
