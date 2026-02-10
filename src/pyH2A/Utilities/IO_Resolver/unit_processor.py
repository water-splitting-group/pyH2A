from typing import Any, Dict, Optional
import pint
from pyH2A.Utilities.Unit_handler.Unit_conversion import UnitConversionHandler


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
