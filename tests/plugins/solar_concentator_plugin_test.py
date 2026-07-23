import pytest
from pyH2A.Plugins.Solar_Concentrator_Plugin import Solar_Concentrator_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF object for Solar_Concentrator_Plugin using variable-value inputs."""

    def __init__(
        self,
        concentration_factor,
        concentrator_cost_per_m2,
        pec_number,
        south_spacing_m,
        ew_spacing_m,
        solar_collection_area_m2,
    ):
        self.inp = {
            "Solar Concentrator": {
                "Concentration factor": {
                    "Value": concentration_factor,
                    "Unit": "-",
                },
                "Cost": {
                    "Value": concentrator_cost_per_m2,
                    "Unit": "USD/m2",
                },
            },
            "PEC Cells": {
                "Number": {
                    "Value": pec_number,
                    "Unit": "-",
                }
            },
            "Land Area Requirement": {
                "South spacing": {
                    "Value": south_spacing_m,
                    "Unit": "m",
                },
                "East/West spacing": {
                    "Value": ew_spacing_m,
                    "Unit": "m",
                },
            },
            "Non-Depreciable Capital Costs": {
                "Solar collection area": {
                    "Value": solar_collection_area_m2,
                    "Unit": "m2",
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "concentration_factor": 1.5,
                "concentrator_cost_per_m2": 300.0,
                "pec_number": 10.0,
                "south_spacing_m": 2.0,
                "ew_spacing_m": 1.5,
                "solar_collection_area_m2": 100.0,
            },
            "expected": {
                "total_solar_collection_area": Quantity(150.0, "m2"),
                "total_land_area": Quantity(225.2772085586298, "m2"),
                "concentrator_cost": Quantity(45000.0, "USD"),
            },
        }
    ],
    ids= [
        "Realistic case - Solar Concentrator Plugin"
    ]
)
def test_solar_concentrator_plugin(case):
    """Test Solar_Concentrator_Plugin using variable-value inputs."""

    # Create DummyDCF
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Solar_Concentrator_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.total_land_area.unit['m2'] == pytest.approx(
        expected["total_land_area"].unit['m2'],
        abs=tolerance
    )
    
    assert plugin.total_solar_collection_area.unit['m2'] == pytest.approx(
        expected["total_solar_collection_area"].unit['m2'],
        abs=tolerance
    )
    
    assert plugin.concentrator_cost.unit['USD'] == pytest.approx(
        expected["concentrator_cost"].unit['USD'],
        abs=tolerance
    )
