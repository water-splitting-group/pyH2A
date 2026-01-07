"""
conversion.py
Handles unit conversion to base units using Pint based on categories defined in units.py.
"""

import pint
from pyH2A.Utilities.units import unit_registry

# Create Pint unit registry
ureg = pint.UnitRegistry()
ureg.define('percent = 0.01 = %')  # Define percent as dimensionless

def to_base_unit(value: float, from_unit: str, category: str):
    """
    Convert a value from its current unit to the base unit of the specified category.

    Parameters
    ----------
    value : float
        Numeric value to convert
    from_unit : str
        Current unit of the value
    category : str
        Unit category whose base unit should be used

    Returns
    -------
    float
        Value converted to the category's base unit

    Notes
    -----
    Assumes that the unit is valid in the category. Does NOT perform validation.
    If the input unit is already the base unit, the value is returned unchanged.
    """
    if category not in unit_registry:
        raise ValueError(f"Unit category '{category}' not found in unit registry")

    base_unit = unit_registry[category]['base_unit']

    # If already in base unit, return as-is
    if from_unit == base_unit:
        return value

    # Convert using Pint
    quantity = value * ureg(from_unit)
    converted = quantity.to(base_unit).magnitude
    return converted
