import pytest
from pyH2A.Plugins.Solar_Thermal_Plugin import Solar_Thermal_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """DCF object for Solar_Thermal_Plugin with configurable inputs."""

    def __init__(
        self,
        design_output_per_day,
        sth_efficiency,
        mean_solar_input,
        additional_land_area,
    ):
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Design output per day": {
                    "Value": design_output_per_day,
                    "Unit": "kg/day",
                }
            },
            "Solar-to-Hydrogen Efficiency": {
                "STH": {
                    "Value": sth_efficiency,
                    "Unit": "-",
                }
            },
            "Solar Input": {
                "Mean solar input": {
                    "Value": mean_solar_input,
                    "Unit": "kW/m2",
                }
            },
            "Non-Depreciable Capital Costs": {
                "Additional land area": {
                    "Value": additional_land_area,
                    "Unit": "-",
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output_per_day": 1000.0,
                "sth_efficiency": 0.14,
                "mean_solar_input": 5.499228123213646/24, # /24 to convert the original kWh / day into kW
                "additional_land_area": 0.0,
            },
            "expected": {
                "area": Quantity(42783.952830200986, "m2"),
            },
        }
    ],
)
def test_solar_thermal_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Solar_Thermal_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.area.unit["m2"] == pytest.approx(
        expected["area"].unit["m2"],
        abs=tolerance
    )