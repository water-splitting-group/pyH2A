import pytest
import numpy as np
from pyH2A.Plugins.Photovoltaic_Plugin import Photovoltaic_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


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
                "Data": {
                    "Value": irradiation_hourly.flatten(), 
                    "Unit": "kWh/m2",
                    "Processed": "Yes"
                }
            },
            "CAPEX Multiplier": {
                "Multiplier": {
                    "Value": capex_multiplier,
                    "Unit": "-"
                }
            },
            "Photovoltaic": {
                "Nominal power": {
                    "Value": nominal_power,
                    "Unit": "kW"
                },
                "CAPEX reference power": {
                    "Value": capex_reference,
                    "Unit": "kW"
                },
                "Power loss per year": {
                    "Value": power_loss_per_year,
                    "Unit": "-"
                },
                "Efficiency": {
                    "Value": efficiency,
                    "Unit": "-"
                },
            },
        }

        self.operation_years = [2026, 2027]


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "irradiation_hourly": np.array([
                    [
                        10.2, 5.2, 12.2, 0, 10.2, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                    ],
                    [
                        10.2, 5.2, 12.2, 0, 10.2, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                    ]
                ]),
                "capex_reference": 960.0,
                "nominal_power": 1000.0,
                "capex_multiplier": 0.6,
                "power_loss_per_year": 0.005,
                "efficiency": 0.2,
            },
            "expected": {
                "pv_scaling_factor": Quantity(0.990984576405111, '-'),
                "area": Quantity(5000.0, 'm2'),
                "energy_generation_yearly_data": {
                    2026: Quantity(np.array([
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.0,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.0, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.0, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.0,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.0, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.3964256642812647, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559,
                        0.0, 0.20209935826103692, 0.4741561866893559, 0.4741561866893559
                    ]), 'kWh'),
                    2027: Quantity(np.array([
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.0,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.0, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.0, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.0,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.0, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.39444353595985837, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091,
                        0.0, 0.20108886146973173, 0.4717854057559091, 0.4717854057559091
                    ]), 'kWh')
                }, 
                "energy_generation_yearly_data_daily_energy": {
                    2026: Quantity(np.array([8.014016860274, 8.014016860274]), 'kWh'),
                    2027: Quantity(np.array([7.9739467759728235, 7.9739467759728235]), 'kWh')
                },
            },
        }
    ],
    ids=[
        "Realistic case - Photovoltaic plugin"
    ]
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

    assert plugin.pv_scaling_factor.unit['-'] == pytest.approx(
        expected["pv_scaling_factor"].unit['-'], 
        abs=tolerance
    )

    assert plugin.area.unit['m2'] == pytest.approx(
        expected["area"].unit['m2'], 
        abs=tolerance
    )

    for year in dcf.operation_years:
        np.testing.assert_allclose(
            plugin.electric_energy_generation_yearly_data[year].unit['J'],
            expected["energy_generation_yearly_data"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )

        np.testing.assert_allclose(
            plugin.electric_energy_generation_yearly_data_daily_power[year].unit["Wh"],
            expected["energy_generation_yearly_data_daily_energy"][year].unit["Wh"],
            rtol=tolerance,
            atol=tolerance,
        )
