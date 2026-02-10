"""
Key matching utilities for the IO_Resolver module.

Provides functions for pattern matching, wildcard detection,
and case-insensitive key lookups in dictionaries.
"""

import re
from typing import Any, Dict, Iterable, List, Optional

from .constants import PARAM_SPEC_KEYS, WILDCARD_PATTERN


def is_param_spec(spec: Any) -> bool:
    """
    Check if a specification dict represents a parameter spec.

    A parameter spec contains hierarchy level keys like 'top_level',
    'mid_level', 'lower_level', or 'bottom_level'.

    Args:
        spec: The specification to check.

    Returns:
        True if spec is a parameter specification dict.

    Example:
        >>> is_param_spec({"top_level": "Table", "mid_level": "Row", "lower_level": "Value"})
        True
        >>> is_param_spec({"type": float})
        False
    """
    return isinstance(spec, dict) and any(k in spec for k in PARAM_SPEC_KEYS)


def is_wildcard_key(key: str) -> bool:
    """
    Check if a key contains a wildcard pattern.

    Args:
        key: The key string to check.

    Returns:
        True if the key contains the wildcard pattern '<...>'.

    Example:
        >>> is_wildcard_key("Table <...>")
        True
        >>> is_wildcard_key("Fixed Table")
        False
    """
    return WILDCARD_PATTERN in key


def match_keys(keys: Iterable[str], pattern: str) -> List[str]:
    """
    Find all keys matching a wildcard pattern.

    Converts the pattern to a regex where '<...>' matches any characters.

    Args:
        keys: Iterable of key strings to search.
        pattern: Pattern string possibly containing '<...>' wildcard.

    Returns:
        List of keys matching the pattern.

    Example:
        >>> match_keys(["Cost Table 1", "Cost Table 2", "Other"], "Cost Table <...>")
        ['Cost Table 1', 'Cost Table 2']
    """
    regex = re.escape(pattern).replace(re.escape(WILDCARD_PATTERN), ".*")
    compiled = re.compile(f"^{regex}$")
    return [key for key in keys if compiled.match(key)]


def find_key_case_insensitive(dictionary: Dict[str, Any], key: str) -> Optional[str]:
    """
    Find a key in a dictionary using case-insensitive matching.

    First checks for an exact match, then falls back to case-insensitive search.

    Args:
        dictionary: The dictionary to search.
        key: The key to find (case-insensitive).

    Returns:
        The actual key from the dictionary, or None if not found.

    Example:
        >>> d = {"MyKey": 1, "Other": 2}
        >>> find_key_case_insensitive(d, "mykey")
        'MyKey'
        >>> find_key_case_insensitive(d, "Missing")
        None
    """
    if key in dictionary:
        return key

    lowered = key.lower()
    for existing in dictionary.keys():
        if existing.lower() == lowered:
            return existing
    return None
