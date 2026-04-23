import pytest
from src.pyH2A.Plugins.Solar_Concentrator_Plugin import Solar_Concentrator_Plugin


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
                "Concentration Factor": {
                    "Value": concentration_factor,
                },
                "Cost ($/m2)": {
                    "Value": concentrator_cost_per_m2,
                },
            },
            "PEC Cells": {
                "Number": {
                    "Value": pec_number,
                }
            },
            "Land Area Requirement": {
                "South Spacing (m)": {
                    "Value": south_spacing_m,
                },
                "East/West Spacing (m)": {
                    "Value": ew_spacing_m,
                },
            },
            "Non-Depreciable Capital Costs": {
                "Solar Collection Area (m2)": {
                    "Value": solar_collection_area_m2,
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
                "pec_number": 10,
                "south_spacing_m": 2.0,
                "ew_spacing_m": 1.5,
                "solar_collection_area_m2": 100.0,
            },
            "expected": {
                "total_solar_collection_area_m2": 150.0,
                "total_land_area_m2": 225.2772085586298,
                "total_land_area_acres": 0.05566712462088022,
                "concentrator_cost": 45000.0,
            },
        }
    ],
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

    assert plugin.total_land_area_m2 == pytest.approx(
        expected["total_land_area_m2"],
        abs=tolerance
    )
    
    assert plugin.total_land_area_acres == pytest.approx(
        expected["total_land_area_acres"],
        abs=tolerance
    )
    
    assert plugin.total_solar_collection_area_m2 == pytest.approx(
        expected["total_solar_collection_area_m2"],
        abs=tolerance
    )
    
    assert plugin.concentrator_cost == pytest.approx(
        expected["concentrator_cost"],
        abs=tolerance
    )
