"""
Constants used across the IO_Resolver module.

This module centralizes magic strings and configuration values
to improve maintainability and reduce duplication.
"""

from typing import FrozenSet

# Keys that have special meaning in input specifications
SPECIAL_KEYS: FrozenSet[str] = frozenset({"optional", "description"})

# Hierarchy level keys for parameter specifications
PARAM_SPEC_KEYS: FrozenSet[str] = frozenset({
    "top_level",
    "mid_level",
    "lower_level",
    "bottom_level",
})

# Wildcard pattern for matching multiple keys
WILDCARD_PATTERN: str = "<...>"

# Value/Unit key conventions
VALUE_KEY: str = "Value"
UNIT_KEY: str = "Unit"
VALUE_SUFFIX: str = "_Value"
UNIT_SUFFIX: str = "_Unit"
