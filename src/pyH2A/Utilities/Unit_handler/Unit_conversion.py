import re
import pint
from pyH2A.Utilities.Unit_handler.Unit_dimension import UnitDimensionHandler
from pyH2A.Utilities.Unit_handler.constants import DIMENSION_TO_UNIT_MAPPING


class UnitConversionHandler:
    """ Handler for unit conversion using pint. """

    def __init__(self):
        """ Initialize the unit registry. """
        self.ureg = pint.UnitRegistry()
        self._register_custom_units()
        self.dimension_handler = UnitDimensionHandler()

    def _register_custom_units(self):
        """Register custom units not in pint's default registry (e.g., currencies)."""
        # Define currency as a new dimension
        self.ureg.define("USD = [currency]")

    def convert(self, value, unit):
        """
        Convert a value with the given unit to SI units.

        Handles both simple units (e.g., 'kg', 'kWh') and compound units
        (e.g., 'kWh/kg' -> 'J/g', 'USD/kWh' -> 'USD/J').

        Parameters
        ----------
        value : float
            The numerical value to convert.
        unit : str
            The unit string (simple or compound).

        Returns
        -------
        pint.Quantity
            The converted quantity with target SI units.
        """
        try:
            target_unit = self._build_target_unit(unit)

            if target_unit is None:
                raise ValueError(f"Cannot determine target unit for '{unit}'.")

            # Special handling for pure temperature conversions (offset units)
            if target_unit == DIMENSION_TO_UNIT_MAPPING["temperature"]:
                quantity = self.ureg.Quantity(value, self.ureg[unit])
                return quantity.to(target_unit)

            quantity = value * self.ureg.Unit(unit)
            return quantity.to(target_unit)
        except pint.errors.UndefinedUnitError as e:
            raise ValueError(str(e)) from e

    def _build_target_unit(self, unit_str):
        """
        Build target SI unit string from a unit string.

        Handles both simple and compound units by parsing operators
        and converting each component to its SI equivalent.

        Parameters
        ----------
        unit_str : str
            The unit string to convert (e.g., 'kWh/kg', 'USD/kWh').

        Returns
        -------
        str
            The target SI unit string (e.g., 'J/g', 'USD/J').
        """
        unit_str = unit_str.strip()

        # Try as a simple unit first
        try:
            dimension = self.dimension_handler.get_dimension(unit_str)
            target = DIMENSION_TO_UNIT_MAPPING.get(dimension)
            if target:
                return target
        except (ValueError, KeyError, Exception):
            pass

        # Handle compound units by splitting on / and *
        # Use regex to split while keeping the operators
        tokens = re.split(r'([/*])', unit_str)
        result_tokens = []

        for token in tokens:
            token = token.strip()
            if token in ['/', '*']:
                result_tokens.append(token)
            elif token:
                # Try to convert this token to its target unit
                target = self._get_component_target(token)
                result_tokens.append(target)

        return ''.join(result_tokens) if result_tokens else unit_str

    def _get_component_target(self, unit_str):
        """
        Get the target SI unit for a single unit component.

        Parameters
        ----------
        unit_str : str
            A simple unit string (e.g., 'kWh', 'kg').

        Returns
        -------
        str
            The target SI unit, or the original if no mapping exists.
        """
        try:
            dimension = self.dimension_handler.get_dimension(unit_str)
            return DIMENSION_TO_UNIT_MAPPING.get(dimension, unit_str)
        except (ValueError, KeyError, Exception):
            # If we can't determine dimension, keep original (e.g., 'USD')
            return unit_str


if __name__ == "__main__":    # Example usage
    handler = UnitConversionHandler()
    print(f"Converted: {handler.convert(1.0, 'kWh/kg')}")
    print(f"Converted: {handler.convert(1.0, 'm3')}")
