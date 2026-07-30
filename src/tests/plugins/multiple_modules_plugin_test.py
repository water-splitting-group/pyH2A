import pytest
import numpy as np
from pyH2A.Plugins.Finance.Multiple_Modules_Plugin import Multiple_Modules_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Multiple_Modules_Plugin with configurable inputs."""

    def __init__(
        self, plant_modules, solar_area_per_module, area_per_staff, shifts, supervisors
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
            "Fixed Operating Costs": {
                "Solar collection area per staffer": {
                    "Value": area_per_staff,
                    "Unit": "m2"
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
                "area_per_staff": 405000.0,
                "shifts": 3,
                "supervisors": 1,
            },
            "expected": {
                "staff_per_module": Quantity(0.6, "-"),
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
