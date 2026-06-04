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
            "TWh": 3.6e15,
            "eV": 1.602176634e-19,
            "cal": 4.184,
            "kcal": 4184.0, 
            "toe": 4.1868e10
        }
    },
    "power": {
        "base": "W",
        "conversions": {
            "W": 1.0,
            "kW": 1e3,
            "MW": 1e6,
            "GW": 1e9,
            "hp": 745.699872, # imperial horsepower 
            "cv": 735.49875,  # metric horsepower
            "J_per_day": 1./86400.,
            "kJ_per_day": 1e3/86400.,
            "MJ_per_day": 1e6/86400.,
            "GJ_per_day": 1e9/86400.,
            "Wh_per_day": 1./24.,
            "kWh_per_day": 1e3/24.,
            "MWh_per_day": 1e6/24.,            
            "GWh_per_day": 1e9/24.,   
            "J_per_year": 1./(86400.*365.),
            "kJ_per_year": 1e3/(86400.*365.),
            "MJ_per_year": 1e6/(86400.*365.),
            "GJ_per_year": 1e9/(86400.*365.),            
            "Wh_per_year": 1./(24.*365.),                     
            "kWh_per_year": 1e3/(24.*365.), 
            "MWh_per_year": 1e6/(24.*365.), 
            "GWh_per_year": 1e9/(24.*365.),             
            "TWh_per_year": 1e12/(24.*365.),             
        }
    },
    "length": {
        "base": "m",
        "conversions": {
            "m": 1.0,
            "mm": 1e-3,
            "cm": 1e-2,
            "km": 1e3, 
            "ft": 0.3048, 
            "in": 0.0254
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
            "km3": 1e9,
            "uL": 1e-9,
            "mL": 1e-6,
            "L": 1e-3,
            "liter": 1e-3,
        }
    },
    "time": {
        "base": "s",
        "conversions": {
            "s": 1.0,
            "ms": 1e-3,
            "minute": 60.0,
            "h": 3600.0,
            "day": 86400.0,
            "week": 604800.0
            "year": 31536000.0, # Assuming 365 days in a year for simplicity
        }
    },
    "currency": {
        "base": "USD",
        "conversions": {
            "USD": 1.0,
            "EUR": 0.8  # Exchange rate should be adjusted via an API or manually when needed
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
            "kmol": 1e3,
            "entity": 1/con.Avogadro, 
            "Nm3": 44.6150334063, # reference 0°C, 1 atm
            "Sm3":  42.2925433799 # reference 15°C, 1 atm
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
            "MPa": 1e6,
            "atm": 101325.0,
            "bar": 1e5,
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
            "F": 9.64853321233100184e4, # Faraday constant
            "Ah": 3600.0,
            "mAh": 3.6, 
            "e": 1.602176634e-19
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

