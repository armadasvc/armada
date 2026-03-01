import copy
from typing import Any


def merge_dicts(default: dict, override: dict) -> dict:
    """
    Recursively merge two dictionaries.
    Override values replace default values.
    """
    for key, value in override.items():
        if isinstance(value, dict) and key in default and isinstance(default[key], dict):
            merge_dicts(default[key], value)
        else:
            default[key] = value
    return default


def find_targeted_index(lst: list, value: Any, key: str) -> int | None:
    """Find the index of a targeted element in a list."""
    for index, d in enumerate(lst):
        if isinstance(d, dict):
            if key in d and d[key] == value:
                return index
            for v in d.values():
                if isinstance(v, (dict, list)):
                    result = find_targeted_index([v] if isinstance(v, dict) else v, value, key)
                    if result is not None:
                        return index
    return None


def merge_messages(
    count: int,
    default_message: dict,
    targeted_messages: list[dict],
    target_key: str,
) -> list[dict]:
    """
    Merge default messages with targeted messages.
    """
    consolidated_messages = []
    for index in range(count):
        targeted_index = find_targeted_index(targeted_messages, index, target_key)

        if targeted_index is not None:
            merged = merge_dicts(
                copy.deepcopy(default_message),
                targeted_messages[targeted_index],
            )
            consolidated_messages.append(merged)
        else:
            consolidated_messages.append(copy.deepcopy(default_message))

    return consolidated_messages
