from typing import Any, Dict, List
import numpy as np
from pyH2A.Utilities.input_modification import process_table
from .constants import VALUE_KEY, WILDCARD_PATTERN


def collect_value_keys(table_spec: Dict[str, Any]) -> List[str]:
    """
    Extract all value keys from a table specification.

    Collects keys containing 'Value' from either wildcard specs
    or explicit row specifications.

    Args:
        table_spec: The specification for a table, either with '<...>'
                   wildcard or explicit row definitions.

    Returns:
        List of unique value keys found in the specification.

    Example:
        >>> spec = {"<...>": {"Value": {...}, "Extra_Value": {...}}}
        >>> collect_value_keys(spec)
        ['Value', 'Extra_Value']
    """
    # Handle wildcard specification
    if WILDCARD_PATTERN in table_spec:
        row_spec = table_spec[WILDCARD_PATTERN]
        return [key for key in row_spec.keys() if VALUE_KEY in key]

    # Handle explicit row specifications
    bottom_keys: List[str] = []
    for _, row_spec in table_spec.items():
        if isinstance(row_spec, dict):
            for key in row_spec.keys():
                if VALUE_KEY in key:
                    bottom_keys.append(key)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(bottom_keys))


def get_safe_value_keys(
    inp: Dict[str, Any],
    top_key: str,
    value_keys: List[str],
) -> List[str]:
    """
    Filter value keys to those that can be safely processed.

    Excludes keys whose values are non-scalar (dicts or arrays)
    that would break the process_table function.

    Args:
        inp: The input dictionary containing all tables.
        top_key: The table name to check.
        value_keys: List of value keys to filter.

    Returns:
        List of value keys that have only scalar values.
    Example:
        Given a table with rows containing 'Usage_Value' and 'Cost_Value',
        if 'Usage_Value' has scalar values but 'Cost_Value' has dicts, then
        this function would return ['Usage_Value'].
    """
    safe_keys: List[str] = []

    for key in value_keys:
        has_non_scalar = False

        for row in inp.get(top_key, {}).values():
            if not isinstance(row, dict) or key not in row:
                continue

            value = row[key]
            if isinstance(value, (dict, np.ndarray)):
                has_non_scalar = True
                break

        if not has_non_scalar:
            safe_keys.append(key)

    return safe_keys


def process_table_for_spec(
    inp: Dict[str, Any],
    top_key: str,
    table_spec: Dict[str, Any],
) -> None:
    """
    Pre-process a table based on its specification.

    Args:
        inp: The input dictionary containing all tables (modified in place).
        top_key: The table name to process.
        table_spec: The specification for this table.

    Note:
        This function modifies the inp dictionary in place.
    """
    value_keys = collect_value_keys(table_spec)
    if not value_keys:
        return

    safe_keys = get_safe_value_keys(inp, top_key, value_keys)
    if safe_keys:

        process_table(inp, top_key, safe_keys)
