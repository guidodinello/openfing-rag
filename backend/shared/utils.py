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
