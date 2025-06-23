from typing import Any


def normalize_json(data: dict[str, Any], separator: str = "_", prefix: str = "") -> dict[str, Any]:
    """Transform a nested dict into a plain dict"""
    result = {}

    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict) and value:  # Non-empty dict
            result.update(normalize_json(value, separator, new_key))
        elif isinstance(value, list):
            # Handle lists by converting to string or flattening if list of dicts
            if value and isinstance(value[0], dict):
                # If list contains dicts, flatten each with index
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        indexed_key = f"{new_key}{separator}{i}"
                        result.update(normalize_json(item, separator, indexed_key))
                    else:
                        result[f"{new_key}{separator}{i}"] = item
            else:
                result[new_key] = value
        else:
            # Primitive value (str, int, float, bool, None)
            result[new_key] = value

    return result


def parse_cli_list_param(param: str) -> list[int]:
    """
    Parse a string into list of integers.

    Examples:
    uv run openchat-downloader agpi --lessons=1,3,5
        "1,3,5" -> [1, 3, 5]
        "1-5" -> [1, 2, 3, 4, 5]
        "1,3-5,7" -> [1, 3, 4, 5, 7]
    """
    if not param:
        return []

    elements: set[int] = set()

    for part in param.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            elements.update(range(start, end + 1))
        else:
            elements.add(int(part))

    return sorted(elements)
