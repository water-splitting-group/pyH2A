import pytest
import numpy as np
from pyH2A.Plugins.Multiple_Modules_Plugin import Multiple_Modules_Plugin


class DummyDCF:
    """DCF object for Multiple_Modules_Plugin with configurable inputs."""

    def __init__(
        self, plant_modules, solar_area_per_module, area_per_staff, shifts, supervisors
    ):
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Plant Modules": {"Value": plant_modules}
            },
            "Non-Depreciable Capital Costs": {
                "Solar Collection Area (m2)": {"Value": solar_area_per_module}
            },
            "Fixed Operating Costs": {
                "area": {"Value": area_per_staff},
                "shifts": {"Value": shifts},
                "supervisor": {"Value": supervisors},
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
                "staff_per_module": 0.6,
            },
        },
    ],
)
def test_multiple_modules_plugin(case):
    """Check Multiple_Modules_Plugin calculates staff per module correctly."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Multiple_Modules_Plugin(dcf, print_info=False)

    assert plugin.staff_per_module == case["expected"]["staff_per_module"]
