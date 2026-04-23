import pytest
import numpy as np
from src.pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin


class DummyDCF:
    """Minimal DCF object for Electrolyzer_Plugin with configurable inputs."""

    def __init__(
        self,
        construction_time,
        capex_multiplier,
        nominal_power_kw,
        capex_reference_power,
        power_increase,
        min_capacity,
        efficiency,
        replacement_time_h,
        available_power_hourly,
    ):

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
        
        self.operation_years = list(available_power_hourly.keys())



@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "construction_time": 2,
                "capex_multiplier": 0.9,
                "nominal_power_kw": 5500.0,
                "capex_reference_power": 1000.0,
                "power_increase": 0.003,
                "min_capacity": 0.10,
                "efficiency": 0.0185,
                "replacement_time_h": 80000.0,
                "available_power_hourly": {
                    2026: np.array(
                        [
                            200000000.2,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            0.0,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                        ]
                    ),
                    2027: np.array(
                        [
                            0.0,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            200500000.2,
                            201200000.2,
                            0.0,
                            201000000.2,
                            206500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            207500000.2,
                            201200000.2,
                            0.0,
                            201000000.2,
                            208500000.2,
                            201200000.2,
                            201200000.2,
                        ]
                    ),
                },
            },
            "expected": {
                "h2_production": np.array([0.0, 0.0, 2035.0, 2035.0]),
                "scaling_factor": 0.9249598065992481,
                "replacement_frequency": 2.0,
                "yearly_data": np.array(
                    [[2026.0, 2035.0, 20.0], [2027.0, 2035.0, 20.0]]
                ),
                "yearly_data_unused_power": {
                    2026: np.array(
                        [
                            197622869.89416197,
                            198122869.89416197,
                            198822869.89416197,
                            198822869.89416197,
                            0.0,
                            198122869.89416197,
                            198822869.89416197,
                            198822869.89416197,
                            198622869.89416197,
                            198122869.89416197,
                            198822869.89416197,
                            198822869.89416197,
                            198622869.89416197,
                            0.0,
                            198822869.89416197,
                            198822869.89416197,
                            198622869.89416197,
                            0.0,
                            198822869.89416197,
                            198822869.89416197,
                            198622869.89416197,
                            0.0,
                            198822869.89416197,
                            198822869.89416197,
                        ]
                    ),
                    2027: np.array(
                        [
                            0.0,
                            198115738.50324446,
                            198815738.50324446,
                            198815738.50324446,
                            198615738.50324446,
                            0.0,
                            198815738.50324446,
                            198815738.50324446,
                            198615738.50324446,
                            198115738.50324446,
                            198815738.50324446,
                            0.0,
                            198615738.50324446,
                            204115738.50324446,
                            198815738.50324446,
                            198815738.50324446,
                            198615738.50324446,
                            205115738.50324446,
                            198815738.50324446,
                            0.0,
                            198615738.50324446,
                            206115738.50324446,
                            198815738.50324446,
                            198815738.50324446,
                        ]
                    ),
                },
                "yearly_data_unused_power_daily": {
                    2026: np.array([3972357397.8832397]),
                    2027: np.array([3992814770.0648894]),
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
    
    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.h2_production,
        expected["h2_production"],
        rtol=tolerance,
        atol=tolerance,
    )

    assert plugin.electrolyzer_scaling_factor == pytest.approx(
        expected["scaling_factor"],
        abs=tolerance
    )
    
    assert plugin.replacement_frequency == pytest.approx(
        expected["replacement_frequency"],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.yearly_data,
        expected["yearly_data"],
        rtol=tolerance,
        atol=tolerance,
    )

    for year in dcf.operation_years:
        np.testing.assert_allclose(
            plugin.yearly_data_unused_power[year],
            expected["yearly_data_unused_power"][year],
            rtol=tolerance,
            atol=tolerance,
        )

        np.testing.assert_allclose(
            plugin.yearly_data_unused_power_daily[year],
            expected["yearly_data_unused_power_daily"][year],
            rtol=tolerance,
            atol=tolerance,
        )
