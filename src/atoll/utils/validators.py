"""Validation utilities."""

import json
from typing import Any, Dict
from pathlib import Path
import jsonschema


def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate configuration against schema."""
    try:
        jsonschema.validate(instance=config, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False


def validate_tool_response(response: Any) -> bool:
    """Validate tool response format."""
    if response is None:
        return False
    
    # Check if response is serializable
    try:
        json.dumps(response)
        return True
    except (TypeError, ValueError):
        return False