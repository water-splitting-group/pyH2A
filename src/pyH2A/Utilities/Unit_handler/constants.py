DIMENSION_TO_UNIT_MAPPING = {
    "energy": "J",
    "length": "m",
    "time": "s",
    "current": "A",
    "luminosity": "cd",
    "mass": "kg",
    "substance": "mol",
    "temperature": "degK",
    "delta_temperature": "degK",
    "volume": "meter**3",
    "currency": "USD"
}

DIMENSION_MAPPING = {
    "[mass] * [length] ** 2 / [time] ** 2": "energy",
    "[length]": "length",
    "[time]": "time",
    "[current]": "current",
    "[luminosity]": "luminosity",
    "[mass]": "mass",
    "[substance]": "substance",
    "[temperature]": "temperature",
    "delta_temperature": "delta_temperature",
    "[length] ** 3": "volume",
    "[meter] ** 3": "volume",
    "dimensionless": "dimensionless",
    "[currency]": "currency"
}

CUSTOM_UNITS = [
    ("USD", "[currency]"),
    ("m3", "[meter] ** 3"),
    ("delta_degK", "delta_temperature"),
    ("delta_degC", "delta_temperature"),
    ("delta_degF", "delta_temperature")
]

# Aliases that pint cannot register as unit names (not valid identifiers).
# These are normalised at parse time in UnitDimensionHandler.get_dimension.
UNIT_ALIASES = {
    "$": "USD",
}
