from functools import reduce
from typing import Any


def deep_get(dictionary: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        dictionary: Dictionary to search (can be None)
        *keys: Sequence of keys to traverse
        default: Default value if path not found

    Returns:
        Value at nested path or default
    """
    result = reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)
    return result if result is not None else default
