import pytest
import numpy as np
from pyH2A.Plugins.Multiple_Modules_Plugin import Multiple_Modules_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Multiple_Modules_Plugin with configurable inputs."""

    def __init__(
        self, 
        plant_modules, 
        solar_area_per_module, 
        battery_modules, 
        number_turbines, 
        area_per_staff, 
        battery_per_staff,
        turbines_per_staff,
        shifts, 
        supervisors
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Plant modules": {
                    "Value": plant_modules,
                    "Unit": "-"
                }
            },
            "Non-Depreciable Capital Costs": {
                "Solar collection area": {
                    "Value": solar_area_per_module,
                    "Unit": "m2"
                }
            },
            "Battery": {
                "Number of needed modules": {
                    "Value": battery_modules,
                    "Unit": "-"
                }
            },    
            "Wind Turbine": {
                "Number of wind turbines": {
                    "Value": number_turbines,
                    "Unit": "-"
                }
            },                         
            "Fixed Operating Costs": {
                "Solar collection area per staffer": {
                    "Value": area_per_staff,
                    "Unit": "m2"
                },
                "Battery modules per staffer": {
                    "Value": battery_per_staff,
                    "Unit": "-"
                },
                "Wind turbines per staffer": {
                    "Value": turbines_per_staff,
                    "Unit": "-"
                },                                
                "Number of 8-hour shifts": {
                    "Value": shifts,
                    "Unit": "-"
                },
                "Number of supervisors": {
                    "Value": supervisors,
                    "Unit": "-"
                },
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_modules": 10,
                "solar_area_per_module": 37500.0,
                "battery_modules":20, 
                "number_turbines":40, 
                "area_per_staff": 405000.0,
                "battery_per_staff":10, 
                "turbines_per_staff":8, 
                "shifts": 3,
                "supervisors": 1,
            },
            "expected": {
                "staff_per_module": Quantity(21.6, "-"),
            },
        },
    ],
    ids=[
        "Realistic case - Multiple Modules Plugin"
    ]
)
def test_multiple_modules_plugin(case):
    """Check Multiple_Modules_Plugin calculates staff per module correctly."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Multiple_Modules_Plugin(dcf, print_info=False)

    assert plugin.staff_per_module.base_value == case["expected"]["staff_per_module"].base_value
