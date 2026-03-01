import csv
import io
import json
from typing import Any


def parse_value(value: Any) -> Any:
    """Recursively parse a value as JSON if possible."""
    if isinstance(value, str):
        value = value.strip()
        if (value.startswith("{") and value.endswith("}")) or (
            value.startswith("[") and value.endswith("]")
        ):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return {k: parse_value(v) for k, v in parsed.items()}
                elif isinstance(parsed, list):
                    return [parse_value(v) for v in parsed]
                return parsed
            except (json.JSONDecodeError, TypeError):
                pass
    return value


def parse_csv_to_list(csv_content: bytes | None) -> list[dict[str, Any]]:
    """Convert CSV content to a list of dictionaries. Returns an empty list if content is empty."""
    if not csv_content:
        return []
    stream = io.StringIO(csv_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    return [{k: parse_value(v) for k, v in row.items()} for row in reader]
