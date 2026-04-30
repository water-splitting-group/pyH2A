"""
Configuration for the custom pyH2A lightweight unit handler.
Defines supported dimensions, base units, and conversions.
"""

from scipy import constants as con

# Temperature handles as a special case because of offsets vs multipliers
ABSOLUTE_TEMPERATURE = {
    "base": "K",
    "supported_units": ["K", "degC"],
    "to_base": {
        "K": lambda x: x,
        "degC": lambda x: x + 273.15,
    },
    "from_base": {
        "K": lambda x: x,
        "degC": lambda x: x - 273.15,
    }
}

# Standard basic dimensions mapping
DIMENSIONS = {
    "energy": {
        "base": "J",
        "conversions": {
            "J": 1.0,
            "kJ": 1e3,
            "MJ": 1e6,
            "GJ": 1e9,
            "Wh": 3600.0,
            "kWh": 3.6e6,
            "MWh": 3.6e9,
            "GWh": 3.6e12,
            "eV": 1.602176634e-19,
            "cal": 4.184,
            "kcal": 4184.0
        }
    },
    "power": {
        "base": "W",
        "conversions": {
            "W": 1.0,
            "kW": 1e3,
            "MW": 1e6,
            "GW": 1e9,
            "hp": 745.699872
        }
    },
    "length": {
        "base": "m",
        "conversions": {
            "m": 1.0,
            "mm": 1e-3,
            "cm": 1e-2,
            "km": 1e3
        }
    },
    "area": {
        "base": "m2",
        "conversions": {
            "m2": 1.0,
            "mm2": 1e-6,
            "cm2": 1e-4,
            "km2": 1e6,
            "acre": 4046.8564224,
            "ha": 1e4
        }
    },
    "volume": {
        "base": "m3",
        "conversions": {
            "m3": 1.0,
            "mm3": 1e-9,
            "cm3": 1e-6,
            "L": 1e-3,
            "liter": 1e-3,
            "km3": 1e9,
            "mL": 1e-6,
            "uL": 1e-9
        }
    },
    "time": {
        "base": "s",
        "conversions": {
            "s": 1.0,
            "minute": 60.0,
            "h": 3600.0,
            "day": 86400.0,
            "year": 31536000.0, # Assuming 365 days in a year for simplicity
            "ms": 1e-3,
            "week": 604800.0
        }
    },
    "currency": {
        "base": "USD",
        "conversions": {
            "USD": 1.0,
            "EUR": 1.0  # Exchange rate should be adjusted via an API or manually when needed
        }
    },
    "mass": {
        "base": "kg",
        "conversions": {
            "kg": 1.0,
            "mg": 1e-6,
            "g": 1e-3,
            "ton": 1000.0  # Note: ton implies metric tonne here
        }
    },
    "temperature_diff": {
        "base": "delta_K",
        "conversions": {
            "delta_K": 1.0,
            "delta_degC": 1.0
        }
    },
    "substance": {
        "base": "mol",
        "conversions": {
            "mol": 1.0,
            "umol": 1e-6,
            "mmol": 1e-3, 
            "entity": 1/con.Avogadro
        }
    },
    "voltage": {
        "base": "V",
        "conversions": {
            "V": 1.0
        }
    },
    "current": {
        "base": "A",
        "conversions": {
            "A": 1.0,
            "mA": 1e-3
        }
    },
    "angle": {
        "base": "rad",
        "conversions": {
            "rad": 1.0,
            "deg": 0.017453292519943295  # pi/180
        }
    },
    "pressure": {
        "base": "Pa",
        "conversions": {
            "Pa": 1.0,
            "hPa": 100.0,
            "atm": 101325.0,
            "bar": 1e5,
            "MPa": 1e6,
            "psi": 6894.757293168
        }
    },
    "force": {
        "base": "N",
        "conversions": {
            "N": 1.0,
            "kN": 1000.0
        }
    },
    "frequency": {
        "base": "Hz",
        "conversions": {
            "Hz": 1.0,
            "kHz": 1e3,
            "MHz": 1e6,
            "GHz": 1e9
        }
    },
    "charge": {
        "base": "C",
        "conversions": {
            "C": 1.0,
            "mC": 1e-3,
            "Ah": 3600.0,
            "mAh": 3.6
        }
    },
    "resistance": {
        "base": "Ohm",
        "conversions": {
            "Ohm": 1.0,
            "mOhm": 1e-3,
            "kOhm": 1e3
        }
    },
    "dimensionless": {
        "base": "-",
        "conversions": {
            "-": 1.0,
            "ppm": 1e-6,
            "ppb": 1e-9
        }
    }
}

# Pre-flattened lookup maps for near-zero latency dimension matching and O(1) operations
FLAT_MULTIPLIERS = {}
FLAT_BASES = {}
FLAT_DIMENSIONS = {}
for dim, data in DIMENSIONS.items():
    b_unit = data["base"]
    for u, f in data["conversions"].items():
        FLAT_MULTIPLIERS[u] = f
        FLAT_BASES[u] = b_unit
        FLAT_DIMENSIONS[u] = dim

for u in ABSOLUTE_TEMPERATURE["supported_units"]:
    FLAT_DIMENSIONS[u] = "absolute_temperature"

