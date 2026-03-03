from typing import Any, Dict, Optional
import pint
from .constants import (
    SPECIAL_KEYS,
    VALUE_KEY,
    UNIT_KEY,
    VALUE_SUFFIX,
    UNIT_SUFFIX,
    WILDCARD_PATTERN,
)
from .key_matcher import (
    is_param_spec,
    is_wildcard_key,
    match_keys,
    find_key_case_insensitive,
)
from .validators import (
    validate_value,
    validate_options,
    check_bounds_on_quantity,
)
from .unit_processor import UnitProcessor
from .table_processor import process_table_for_spec


class InputResolver:
    """
    Resolve and validate inputs from dcf.inp based on a schema-like input_dict.

    This class takes a specification dictionary that describes the expected
    structure and constraints of input data, then resolves and validates
    the actual values from dcf.inp.

    Attributes:
        dcf: The DCF object containing the inp dictionary.
        plugin_name: Name used in error messages for context.
        unit_processor: Handles unit conversions.

    Example:
        >>> resolver = InputResolver(dcf, plugin_name="MyPlugin")
        >>> spec = {
        ...     "Parameters": {
        ...         "Efficiency": {
        ...             "Value": {"type": float, "bounds": (0, 1)},
        ...         }
        ...     }
        ... }
        >>> result = resolver.resolve(spec)
    """

    def __init__(
        self,
        dcf,
        plugin_name: Optional[str] = None,
        unit_registry: Optional[pint.UnitRegistry] = None,
    ):
        """
        Initialize the InputResolver.

        Args:
            dcf: The DCF object containing inp dictionary with input data.
            plugin_name: Name for error messages (default: "input_resolver").
            unit_registry: Optional pint UnitRegistry for unit handling.
        """
        self.dcf = dcf
        self.plugin_name = plugin_name or "input_resolver"
        self.unit_processor = UnitProcessor(unit_registry)

    @property
    def ureg(self) -> pint.UnitRegistry:
        """Access the pint UnitRegistry."""
        return self.unit_processor.ureg

    def resolve(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve all inputs according to the provided specification.

        Processes each entry in input_dict, handling parameter specs,
        wildcard patterns, and explicit table specifications.

        Args:
            input_dict: Specification dictionary defining expected structure.

        Returns:
            Dictionary of resolved values with units as pint Quantities.
        """
        resolved: Dict[str, Any] = {}

        for key, spec in input_dict.items():
            if is_param_spec(spec):
                resolved[key] = self._resolve_param_spec(spec)
            elif is_wildcard_key(key):
                resolved.update(self._resolve_table_group(key, spec))
            else:
                resolved[key] = self._resolve_table(key, spec)

        return resolved

    # -------------------------------------------------------------------------
    # Parameter Spec Resolution
    # explain what this function does and how it uses the keys 'top_level',
    # 'mid_level', 'bottom_level' to resolve parameters.
    # -------------------------------------------------------------------------

    def _resolve_param_spec(self, spec: Dict[str, Any]) -> Any:
        """Resolve a single parameter specification.
        A parameter specification is a dict that contains hierarchy level keys
        such as 'top_level', 'mid_level', 'bottom_level'.
        The function extracts these keys to determine where in the dcf.inp
        structure to look for the value. It then resolves the value according
        to the specification, including handling units if it's a Value field.
        """
        top_key = spec.get("top_level")
        mid_key = spec.get("mid_level")
        bottom_key = spec.get("bottom_level")

        if top_key is None or mid_key is None or bottom_key is None:
            raise KeyError(
                f"{self.plugin_name}: Parameter spec missing required key(s)."
            )

        # Handle wildcard in top_key
        if is_wildcard_key(top_key):
            return self._resolve_table_group(
                top_key, {WILDCARD_PATTERN: {bottom_key: spec}}
            )

        # Handle wildcard in mid_key
        if is_wildcard_key(mid_key):
            if isinstance(bottom_key, dict):
                return self._resolve_table(top_key, {WILDCARD_PATTERN: bottom_key})
            return self._resolve_table(
                top_key, {WILDCARD_PATTERN: {bottom_key: spec}}
            )

        # Handle explicit hierarchy
        if isinstance(bottom_key, dict):
            process_table_for_spec(self.dcf.inp, top_key, {
                                   mid_key: bottom_key})
            return self._resolve_row(
                top_key, mid_key, self.dcf.inp[top_key][mid_key], bottom_key
            )

        process_table_for_spec(self.dcf.inp, top_key, {
                               mid_key: {bottom_key: spec}})
        return self._resolve_specific_value(top_key, mid_key, bottom_key, spec)

    # -------------------------------------------------------------------------
    # Table Resolution
    # -------------------------------------------------------------------------

    def _resolve_table_group(
        self, top_pattern: str, table_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve multiple tables matching a wildcard pattern."""
        matching_keys = match_keys(self.dcf.inp.keys(), top_pattern)

        if not matching_keys:
            raise KeyError(
                f"{self.plugin_name}: No tables found matching pattern '{top_pattern}'."
            )

        return {key: self._resolve_table(key, table_spec) for key in matching_keys}

    def _resolve_table(
        self, top_key: str, table_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a single table according to its specification."""
        actual_top_key = find_key_case_insensitive(self.dcf.inp, top_key)
        if actual_top_key is None:
            raise KeyError(f"{self.plugin_name}: Missing table '{top_key}'.")

        process_table_for_spec(self.dcf.inp, actual_top_key, table_spec)

        # Handle wildcard row specification
        if WILDCARD_PATTERN in table_spec:
            row_spec = table_spec[WILDCARD_PATTERN]
            return self._resolve_all_rows(actual_top_key, row_spec)

        # Handle explicit row specifications
        return self._resolve_explicit_rows(actual_top_key, table_spec)

    def _resolve_all_rows(
        self, top_key: str, row_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve all rows in a table using a single row specification.
        Example: If the table has rows 'Row1', 'Row2', etc., and the spec is given as
        {'<...>': { ... }}, then this function applies the same resolution logic to
        each row in the table using the provided row_spec.
        """
        resolved_table = {
            mid_key: self._resolve_row(top_key, mid_key, row, row_spec)
            for mid_key, row in self.dcf.inp[top_key].items()
        }

        return resolved_table

    def _resolve_explicit_rows(
        self, top_key: str, table_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve explicitly specified rows in a table."""
        resolved_table: Dict[str, Any] = {}

        for mid_key, row_spec in table_spec.items():
            if mid_key in SPECIAL_KEYS:
                continue

            actual_mid_key = find_key_case_insensitive(
                self.dcf.inp[top_key], mid_key
            )

            if actual_mid_key is None:
                if row_spec.get("optional") is True:
                    continue
                raise KeyError(
                    f"{self.plugin_name}: Missing key '{top_key} > {mid_key}'."
                )

            row = self.dcf.inp[top_key][actual_mid_key]
            resolved_table[actual_mid_key] = self._resolve_row(
                top_key, actual_mid_key, row, row_spec
            )

        return resolved_table

    # -------------------------------------------------------------------------
    # Row Resolution
    # -------------------------------------------------------------------------

    def _resolve_row(
        self,
        top_key: str,
        mid_key: str,
        row: Dict[str, Any],
        row_spec: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve a single row according to its specification.

        example input:
        {
            'Usage_Value': {
                'type': {float, int},
                'bounds': (0, None)
            },
            'Usage_Unit': {
                'dimension': 'energy / mass'
            },
            'Cost_Value': {
                'type': {float, int},
                'bounds': (0, None)
            },
            'Cost_Unit': {
                'dimension': 'currency / energy'
            },
            'Type': {
                'type': str,
                'options': {'electricity', 'natural_gas', 'water'}
            }
        }

        output:
        {
           'Usage_Value': '<Quantity 1E9 J/kg>',
           'Cost_Value': '<Quantity 2E-8 USD/J>',
           'Type': 'natural_gas'
        }

        """
        resolved_row: Dict[str, Any] = {}
        context_base = f"{top_key} > {mid_key}"

        for key, spec in row_spec.items():
            if key in SPECIAL_KEYS:
                continue

            result = self._resolve_field(
                row, key, spec, context_base, row_spec)
            if result is not None:
                resolved_row[key] = result

        return resolved_row

    def _resolve_field(
        self,
        row: Dict[str, Any],
        key: str,
        spec: Dict[str, Any],
        context_base: str,
        row_spec: Dict[str, Any],
    ) -> Any:
        """Resolve a single field within a row."""
        context = f"{context_base} > {key}"

        # Check if field exists
        if key not in row:
            if row_spec.get("optional") is True:
                return None
            raise KeyError(f"{self.plugin_name}: Missing key '{context}'.")

        value = row[key]

        # Handle Value fields (require unit conversion)
        if VALUE_KEY in key:
            # Determine corresponding unit key and pull its dimension spec so we
            # can validate the unit's dimension before conversion.
            unit_key = (
                UNIT_KEY if key == VALUE_KEY
                else key.replace(VALUE_SUFFIX, UNIT_SUFFIX)
            )
            unit_spec = row_spec.get(unit_key)
            expected_dimension = (
                unit_spec.get("dimension")
                if isinstance(unit_spec, dict)
                else None
            )
            return self._resolve_value_field(
                row, key, spec, context, expected_dimension
            )

        # Skip Unit fields (handled with Value fields)
        if key.endswith(UNIT_SUFFIX) or key == UNIT_KEY:
            return None

        # Handle regular fields
        validate_value(value, spec, context, check_bounds_flag=True)
        validate_options(value, spec.get("options"), context)
        return value

    def _resolve_value_field(
        self,
        row: Dict[str, Any],
        key: str,
        spec: Dict[str, Any],
        context: str,
        expected_dimension: Optional[str] = None,
    ) -> Any:
        """Resolve a Value field with its associated unit."""
        # Determine corresponding unit key
        unit_key = UNIT_KEY if key == VALUE_KEY else key.replace(
            VALUE_SUFFIX, UNIT_SUFFIX)

        if unit_key not in row:
            raise KeyError(
                f"{self.plugin_name}: Missing unit '{context.rsplit(' > ', 1)[0]} > {unit_key}' "
                f"for '{key}'."
            )

        value = row[key]
        unit_str = row[unit_key]

        # Validate the raw value
        validate_value(value, spec, context, check_bounds_flag=False)

        # Check unit dimension matches the spec before converting
        if expected_dimension is not None:
            self.unit_processor.validate_unit_dimension(
                unit_str, expected_dimension
            )

        # Convert with unit
        resolved = self.unit_processor.convert_value_with_unit(
            value, unit_str)

        # Check bounds on the converted quantity
        bounds = spec.get("bounds")
        if bounds is not None:
            check_bounds_on_quantity(resolved, bounds, context)
        return resolved

    def _resolve_specific_value(
        self,
        top_key: str,
        mid_key: str,
        bottom_key: str,
        value_spec: Dict[str, Any],
    ) -> Any:
        """Resolve a specific value from a known path."""
        actual_mid_key = find_key_case_insensitive(
            self.dcf.inp[top_key], mid_key
        )
        if actual_mid_key is None:
            raise KeyError(
                f"{self.plugin_name}: Missing key '{top_key} > {mid_key}'."
            )

        row = self.dcf.inp[top_key][actual_mid_key]
        if bottom_key not in row:
            raise KeyError(
                f"{self.plugin_name}: Missing key '{top_key} > {actual_mid_key} > {bottom_key}'."
            )

        # Build row spec for resolution
        row_spec = {bottom_key: value_spec}
        unit_key = (
            UNIT_KEY if bottom_key == VALUE_KEY
            else bottom_key.replace(VALUE_SUFFIX, UNIT_SUFFIX)
        )
        if unit_key in row:
            row_spec[unit_key] = {"dimension": value_spec.get("dimension")}

        return self._resolve_row(top_key, actual_mid_key, row, row_spec).get(bottom_key)


# -----------------------------------------------------------------------------
# Convenience Function
# -----------------------------------------------------------------------------

def input_resolver(
    dcf,
    input_dict: Dict[str, Any],
    plugin_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper for InputResolver.

    Args:
        dcf: The DCF object containing inp dictionary.
        input_dict: Specification dictionary defining expected structure.
        plugin_name: Name for error messages (default: "input_resolver").

    Returns:
        Dictionary of resolved values with units as pint Quantities.

    Example:
        >>> result = input_resolver(dcf, {"Table": {"Row": {"Value": {...}}}})
    """
    return InputResolver(dcf, plugin_name=plugin_name).resolve(input_dict)
