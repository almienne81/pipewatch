"""Tag support for pipeline runs — attach arbitrary key/value labels to runs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_TAG_RE = re.compile(r'^[a-zA-Z0-9_.-]+$')


class TagError(ValueError):
    """Raised when a tag key or value is invalid."""


@dataclass
class Tags:
    """Immutable-ish collection of string key/value tags."""
    _data: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or not _TAG_RE.match(key):
            raise TagError(
                f"Invalid tag key {key!r}: must be non-empty and match [a-zA-Z0-9_.-]+"
            )

    @staticmethod
    def _validate_value(value: str) -> None:
        if not isinstance(value, str):
            raise TagError(f"Tag value must be a string, got {type(value).__name__}")

    def set(self, key: str, value: str) -> "Tags":
        """Return a new Tags instance with the given key set."""
        self._validate_key(key)
        self._validate_value(value)
        new_data = dict(self._data)
        new_data[key] = value
        return Tags(new_data)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, str]:
        return dict(self._data)

    def to_list(self) -> List[str]:
        """Render as list of 'key=value' strings (useful for CLI display)."""
        return [f"{k}={v}" for k, v in sorted(self._data.items())]

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:  # pragma: no cover
        return f"Tags({self._data!r})"


def parse_tags(raw: List[str]) -> Tags:
    """Parse a list of 'key=value' strings into a Tags instance.

    Args:
        raw: e.g. ["env=prod", "team=data"]

    Returns:
        Tags instance

    Raises:
        TagError: if any entry is malformed or key is invalid.
    """
    tags = Tags()
    for item in raw:
        if '=' not in item:
            raise TagError(f"Tag {item!r} must be in 'key=value' format")
        key, _, value = item.partition('=')
        tags = tags.set(key.strip(), value.strip())
    return tags


def tags_from_dict(data: Dict[str, str]) -> Tags:
    """Reconstruct Tags from a plain dict (e.g. loaded from JSON/YAML)."""
    tags = Tags()
    for k, v in data.items():
        tags = tags.set(k, v)
    return tags
