DIMENSION_TO_UNIT_MAPPING = {
    "energy": "J",
    "length": "m",
    "time": "s",
    "current": "A",
    "luminosity": "cd",
    "mass": "g",
    "substance": "mol",
    "temperature": "degK",
    "volume": "l",
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
    "[length] ** 3": "volume",
    "[meter] ** 3": "volume",
    "dimensionless": "dimensionless",
    "[currency]": "currency"
}

CUSTOM_UNITS = [
    ("USD", "[currency]"),
    ("m3", "[meter] ** 3"),
]
