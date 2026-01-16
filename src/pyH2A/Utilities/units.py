import pint

# Create Pint unit registry
ureg = pint.UnitRegistry()
ureg.define('percent = 0.01 = %')  # Define percent as dimensionless
ureg.define("TCE = 29.3076 * gigajoule")
ureg.define("TOE = 41.868 * gigajoule")
ureg.define("fraction = 1 * dimensionless = frac")

dimension = {
    "Energy_Battery": {
        "base_unit": ureg.kWh,  
        "allowed_units": {ureg.kWh, ureg.MJ, ureg.J, ureg.kJ, ureg.Wh,
                          ureg.MWh, ureg.GJ, ureg.TJ, ureg.PJ, ureg.BTU,
                          ureg.TCE, ureg.TOE},
    },
    "Dimensionless": {
        "base_unit": ureg.dimensionless,  
        "allowed_units": {ureg.dimensionless, ureg.percent, ureg.fraction},
    },
}

def validate_unit_for_category(category: str, unit: pint.Unit):
    if category not in dimension:
        raise ValueError(f"Unknown category '{category}'")

    allowed_units = dimension[category]["allowed_units"]
    if unit not in allowed_units:
        msg = f"Unit '{unit}' is not allowed in category '{category}'. Allowed: {allowed_units}"
        raise ValueError(msg)

    return True

def convert_dict_values_to_base(value_dict, current_unit, category):
    """
    Convert all numeric values in a dict-of-lists to base units.
    
    Parameters
    ----------
    value_dict : dict
        Dict of years → list of values.
    current_unit : str
        Current unit string.
    category : str
        Unit category for conversion.
    
    Returns
    -------
    dict
        Converted dict-of-lists, base unit applied.
    """
    converted = {}
    for year, values in value_dict.items():
        converted[year] = [to_base_unit(v, current_unit, category) for v in values]
    return converted


def to_base_unit(value: float, from_unit: str, category: str):
    """
    Convert a value from its current unit to the base unit of the specified category.
    Raises a clear error if Pint cannot perform the conversion.
    """
    if validate_unit_for_category(category, ureg.Unit(from_unit)):
            
        base_unit = dimension[category]['base_unit']

        try:
            if isinstance(value, dict):
                return convert_dict_values_to_base(value, from_unit, category)
            else:    
                quantity = value * ureg.Unit(from_unit)
                converted = quantity.to(base_unit)
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