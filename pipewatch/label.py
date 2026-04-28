"""Label management for pipeline runs — attach arbitrary key/value metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_VALUE_MAX = 256


class LabelError(ValueError):
    """Raised when a label key or value is invalid."""


def _validate_key(key: str) -> None:
    if not isinstance(key, str) or not _KEY_RE.match(key):
        raise LabelError(
            f"Invalid label key {key!r}: must match [a-z][a-z0-9_-]{{0,63}}"
        )


def _validate_value(value: str) -> None:
    if not isinstance(value, str):
        raise LabelError(f"Label value must be a str, got {type(value).__name__}")
    if len(value) > _VALUE_MAX:
        raise LabelError(
            f"Label value too long ({len(value)} chars); max is {_VALUE_MAX}"
        )


@dataclass(frozen=True)
class Labels:
    """Immutable collection of string key/value labels."""

    _data: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation (returns new instance)
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> "Labels":
        """Return a new Labels with *key* set to *value*."""
        _validate_key(key)
        _validate_value(value)
        return Labels({**self._data, key: value})

    def remove(self, key: str) -> "Labels":
        """Return a new Labels without *key* (no-op if absent)."""
        data = {k: v for k, v in self._data.items() if k != key}
        return Labels(data)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._data.get(key, default)

    def keys(self) -> List[str]:
        return sorted(self._data.keys())

    def items(self) -> List[tuple]:
        return [(k, self._data[k]) for k in self.keys()]

    def matches(self, selector: Dict[str, str]) -> bool:
        """Return True if all selector key/value pairs are present."""
        return all(self._data.get(k) == v for k, v in selector.items())

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, str]:
        return dict(self._data)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Labels":
        instance = cls()
        for k, v in data.items():
            instance = instance.set(k, v)
        return instance

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __repr__(self) -> str:  # pragma: no cover
        return f"Labels({self._data!r})"
