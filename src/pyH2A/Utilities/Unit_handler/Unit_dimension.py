import pint
from pyH2A.Utilities.Unit_handler.constants import CUSTOM_UNITS, DIMENSION_MAPPING


class UnitDimensionHandler:
    """Handler for unit dimension detection and validation using pint."""

    def __init__(self):
        """Initialize the unit registry."""
        self.ureg = pint.UnitRegistry()
        for unit_name, definition in CUSTOM_UNITS:
            try:
                self.ureg.Unit(unit_name)
            except (pint.UndefinedUnitError, pint.errors.UndefinedUnitError):
                self.ureg.define(f"{unit_name} = {definition}")
            except Exception:
                pass

    def get_dimension(self, unit_str):
        try:
            unit = self.ureg.Unit(unit_str)
        except Exception:
            raise ValueError(
                f"'{unit_str}' is not a valid unit. Please provide a valid unit.")

        dimensionality_str = str(unit.dimensionality)
        dimension = DIMENSION_MAPPING.get(dimensionality_str)

        if dimension is None:
            raise ValueError(
                f"'{unit_str}' is not a recognized or supported unit in this context.")

        return dimension
