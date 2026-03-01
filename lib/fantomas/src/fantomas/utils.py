import json


def get_value_or_default(value, default):
    """Return value if not None, otherwise return default."""
    return value if value is not None else default


def load_config(config):
    """Load configuration from file path or return dict as-is.

    Args:
        config: Either a file path (str) to a JSON file or a dict

    Returns:
        dict: The configuration dictionary
    """
    if isinstance(config, str):
        with open(config, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return config
