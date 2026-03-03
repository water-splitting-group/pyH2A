from typing import Any, Optional
import pint
from pyH2A.Utilities.Unit_handler.Unit_conversion import UnitConversionHandler
from pyH2A.Utilities.Unit_handler.Unit_dimension import UnitDimensionHandler


class UnitProcessor:
    """
    Handles unit normalization and value conversion.

    Wraps pint UnitRegistry and UnitConversionHandler to provide
    a clean interface for unit operations.

    Attributes:
        ureg: The pint UnitRegistry instance.
        converter: The UnitConversionHandler for complex conversions.
    """

    def __init__(self, unit_registry: Optional[pint.UnitRegistry] = None):
        """
        Initialize the UnitProcessor.

        Args:
            unit_registry: Optional pint UnitRegistry. Creates a new one if not provided.
        """
        self.ureg = unit_registry or pint.UnitRegistry()
        self.converter = UnitConversionHandler()
        self.dimension_handler = UnitDimensionHandler()

    def convert_single_value(self, value: Any, unit: str) -> pint.Quantity:
        """
        Convert a single value with its unit to a pint Quantity.

        Handles percentages specially by converting to dimensionless.

        Args:
            value: The numeric value to convert.
            unit: The normalized unit string.

        Returns:
            A pint Quantity with the value and unit.

        Example:
            >>> processor.convert_single_value(100, "kg")
            <Quantity(100, 'kilogram')>
        """

        if unit == "percent":
            return (value * self.ureg.Unit("percent")).to("dimensionless")

        val = self.converter.convert(value, unit)
        return val

    def convert_value_with_unit(self, value: Any, unit_str: str) -> Any:
        """
        Convert a value (scalar or dict) with its unit.

        Handles both single values and dictionaries of values.

        Args:
            value: A numeric value or dict of numeric values.
            unit_str: The unit string (will be normalized).

        Returns:
            A pint Quantity or dict of Quantities.

        Example:
            >>> processor.convert_value_with_unit({"a": 1, "b": 2}, "kg")
            {'a': <Quantity(1, 'kilogram')>, 'b': <Quantity(2, 'kilogram')>}
        """

        if isinstance(value, dict):
            return {
                k: self.convert_single_value(v, unit_str)
                for k, v in value.items()
            }

        return self.convert_single_value(value, unit_str)

    def validate_unit_dimension(
        self, unit_str: str, expected_dimension: str
    ) -> None:
        """
        Validate that a unit string is dimensionally consistent with an expected
        dimension label (e.g. 'energy / mass').

        Delegates to UnitDimensionHandler.get_dimension, which uses pint to map
        a unit's dimensionality to a recognised label. Each token in the compound
        expected_dimension string (e.g. 'energy', 'mass') is resolved to its
        canonical SI unit via get_dimension, building an expression that pint can
        compare against the actual unit.

        Args:
            unit_str: The unit string to check (e.g. 'kWh/kg').
            expected_dimension: Dimension label from the spec (e.g. 'energy / mass').
            context: Location string used in error messages.

        Raises:
            ValueError: If the unit's dimensionality does not match the expected
                dimension, or if either string cannot be parsed.
        """

        if '/' in unit_str:
            units = [part.strip() for part in unit_str.split('/')]

            if len(units) != 2:
                raise ValueError(
                    f"Invalid compound unit '{unit_str}'. Only one '/' operator is supported.")
            dimensions = [part.strip()
                          for part in expected_dimension.split('/')]
            if len(dimensions) != 2:
                raise ValueError(
                    f"Invalid expected dimension '{expected_dimension}'. Only one '/' operator is supported.")

            unit_dim_1 = self.dimension_handler.get_dimension(units[0])

            unit_dim_2 = self.dimension_handler.get_dimension(units[1])

            if unit_dim_1 != dimensions[0] or unit_dim_2 != dimensions[1]:
                raise ValueError(
                    f"Unit '{unit_str}' has dimensions '{unit_dim_1} / {unit_dim_2}', which does not match expected dimension '{expected_dimension}'.")
        else:
            unit_dim = self.dimension_handler.get_dimension(unit_str)
            if unit_dim != expected_dimension.strip():
                raise ValueError(
                    f"Unit '{unit_str}' has dimension '{unit_dim}', which does not match expected dimension '{expected_dimension}'.")
