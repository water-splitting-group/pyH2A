import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin


class DummyDCF:
    """Minimal DCF object for Electrolyzer_Plugin with configurable inputs."""

    def __init__(
        self,
        available_power_hourly,
        nominal_power_kw,
        efficiency,
        min_capacity,
        power_increase,
        construction_time,
        capex_multiplier,
        capex_reference_power,
        replacement_time_h,
    ):
        self.operation_years = list(available_power_hourly.keys())

        self.inp = {
            "Financial Input Values": {
                "construction time": {"Value": construction_time}
            },
            "CAPEX Multiplier": {"Multiplier": {"Value": capex_multiplier}},
            "Electrolyzer": {
                "Nominal Power (kW)": {"Value": nominal_power_kw},
                "CAPEX Reference Power (kW)": {"Value": capex_reference_power},
                "Power requirement increase per year": {"Value": power_increase},
                "Minimum capacity": {"Value": min_capacity},
                "Conversion efficiency (kg H2/kWh)": {"Value": efficiency},
                "Replacement time (h)": {"Value": replacement_time_h},
            },
            "Power Generation": {
                "Available Power (hourly, kWh)": {
                    "Value": available_power_hourly,
                    "Processed": "Yes",
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "available_power_hourly": {
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
                    2027: np.array(
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
                "nominal_power_kw": 5500.0,
                "efficiency": 0.0185,
                "min_capacity": 0.10,
                "power_increase": 0.003,
                "construction_time": 0,
                "capex_multiplier": 1.0,
                "capex_reference_power": 1000.0,
                "replacement_time_h": 80000.0,
            },
            "expected": {
                "h2_production": np.array([0.0, 0.0]),
                "scaling_factor": 1.0,
                "replacement_frequency": 2.0,
                "yearly_data": np.array([[2026.0, 0.0, 0.0], [2027.0, 0.0, 0.0]]),
                "yearly_data_unused_power": {
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
                    2027: np.array(
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
                "yearly_data_unused_power_daily": {
                    2026: np.array([238.8]),
                    2027: np.array([238.8]),
                },
            },
        },
    ],
)
def test_electrolyzer_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Electrolyzer_Plugin(dcf, print_info=False)
    expected = case["expected"]

    np.testing.assert_allclose(
        plugin.h2_production,
        expected["h2_production"],
        rtol=1e-9,
        atol=1e-9,
    )

    assert plugin.electrolyzer_scaling_factor == expected["scaling_factor"]
    assert plugin.replacement_frequency == expected["replacement_frequency"]

    np.testing.assert_allclose(
        plugin.yearly_data,
        expected["yearly_data"],
        rtol=1e-9,
        atol=1e-9,
    )

    for year in dcf.operation_years:

        np.testing.assert_allclose(
            plugin.yearly_data_unused_power[year],
            expected["yearly_data_unused_power"][year],
            rtol=1e-9,
            atol=1e-9,
        )

        np.testing.assert_allclose(
            plugin.yearly_data_unused_power_daily[year],
            expected["yearly_data_unused_power_daily"][year],
            rtol=1e-9,
            atol=1e-9,
        )
