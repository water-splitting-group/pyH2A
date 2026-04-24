import pytest
from pyH2A.Plugins.Solar_Thermal_Plugin import Solar_Thermal_Plugin


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
                "Design Output per Day": {"Value": design_output_per_day}
            },
            "Solar-to-Hydrogen Efficiency": {
                "STH (%)": {"Value": sth_efficiency}
            },
            "Solar Input": {
                "Mean solar input (kWh/m2/day)": {"Value": mean_solar_input}
            },
            "Non-Depreciable Capital Costs": {
                "Additional Land Area (%)": {"Value": additional_land_area}
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output_per_day": 1000,
                "sth_efficiency": 0.14,
                "mean_solar_input": 5.499228123213646,
                "additional_land_area": 0,
            },
            "expected": {
                "area_acres": 10.572124480592073,
                "area_m2": 42783.93590009135,
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

    assert plugin.area_acres == expected["area_acres"]
    assert plugin.area_m2 == expected["area_m2"]
