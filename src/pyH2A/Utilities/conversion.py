import pint
from pyH2A.Utilities.units import unit_registry

# Create Pint unit registry
ureg = pint.UnitRegistry()
ureg.define('percent = 0.01 = %')  # Define percent as dimensionless

def to_base_unit(value: float, from_unit: str, category: str):
    """
    Convert a value from its current unit to the base unit of the specified category.
    Raises a clear error if Pint cannot perform the conversion.
    """
    if category not in unit_registry:
        raise ValueError(f"Unit category '{category}' not found in unit registry")

    base_unit = unit_registry[category]['base_unit']

    # If already in base unit, return as-is
    if from_unit == base_unit:
        return value

    try:
        quantity = value * ureg(from_unit)
        converted = quantity.to(base_unit).magnitude
        return converted

    except pint.errors.UndefinedUnitError as e:
        raise ValueError(
            f"Undefined unit '{from_unit}'. Pint does not recognize this unit."
        ) from e

    except pint.errors.DimensionalityError as e:
        raise ValueError(
            f"Cannot convert from '{from_unit}' to '{base_unit}': units are not dimensionally compatible."
        ) from e

    except pint.errors.PintError as e:
        # Catch-all for other Pint-related issues
        raise ValueError(
            f"Unit conversion failed for '{from_unit}' → '{base_unit}': {e}"
        ) from e