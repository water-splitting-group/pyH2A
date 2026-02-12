import pytest
import numpy as np
from pyH2A.Plugins.Photovoltaic_Plugin import Photovoltaic_Plugin


class DummyDCF:
    """Minimal DCF object for Photovoltaic_Plugin testing with configurable inputs."""

    def __init__(
        self,
        irradiation_hourly,
        capex_multiplier,
        nominal_power,
        capex_reference,
        power_loss_per_year,
        efficiency,
    ):

        self.inp = {
            "Irradiation Used": {
                "Data": {"Value": irradiation_hourly[2026], "Processed": "Yes"}
            },
            "CAPEX Multiplier": {"Multiplier": {"Value": capex_multiplier}},
            "Photovoltaic": {
                "Nominal Power (kW)": {"Value": nominal_power},
                "CAPEX Reference Power (kW)": {"Value": capex_reference},
                "Power loss per year": {"Value": power_loss_per_year},
                "Efficiency": {"Value": efficiency},
            },
        }

        self.operation_years = list(irradiation_hourly.keys())


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "irradiation_hourly": {
                    2026: np.array(
                        [
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                            10.2,
                            5.2,
                            12.2,
                            12.2,
                        ]
                    ),
                },
                "capex_reference": 1000.0,
                "nominal_power": 1000.0,
                "capex_multiplier": 1.0,
                "power_loss_per_year": 0.005,
                "efficiency": 0.2,
            },
            "expected": {
                "pv_scaling_factor": 1.0,
                "area_m2": 5000.0,
                "area_acres": 1.235525,
                "power_generation_yearly_data": {
                    2026: np.array(
                        [
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                            0.3964256642812647,
                            0.20209935826103692,
                            0.4741561866893559,
                            0.4741561866893559,
                        ]
                    )
                },
                "power_generation_yearly_data_daily_power": {
                    2026: np.array([9.28102437552608])
                },
            },
        }
    ],
)
def test_photovoltaic_plugin(case):
    """Test Photovoltaic_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Photovoltaic_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.pv_scaling_factor == pytest.approx(
        expected["pv_scaling_factor"], 
        abs=tolerance
    )

    assert plugin.area_m2 == pytest.approx(
        expected["area_m2"], 
        abs=tolerance
    )

    assert plugin.area_acres == pytest.approx(
        expected["area_acres"], 
        abs=tolerance
    )

    for year in dcf.operation_years:
        np.testing.assert_allclose(
            plugin.power_generation_yearly_data[year],
            expected["power_generation_yearly_data"][year],
            rtol=tolerance,
            atol=tolerance,
        )
        
        np.testing.assert_allclose(
            plugin.power_generation_yearly_data_daily_power[year],
            expected["power_generation_yearly_data_daily_power"][year],
            rtol=tolerance,
            atol=tolerance,
        )
