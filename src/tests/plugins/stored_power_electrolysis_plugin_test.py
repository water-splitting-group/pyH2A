import pytest
import numpy as np
from pyH2A.Plugins.Stored_Power_Electrolysis_Plugin import Stored_Power_Electrolysis_Plugin


class DummyDCF:
    """Minimal DCF for Stored_Power_Electrolysis_Plugin with variable-value inputs."""

    def __init__(
        self,
        fraction_stored_power_for_electrolysis,
        electrolyzer_nominal_power_kW,
        electrolyzer_power_increase_per_year,
        electrolyzer_min_capacity,
        electrolyzer_conversion_efficiency,
        electrolyzer_replacement_time_h,
        electrolyzer_yearly_H2_production_kg,
        electrolyzer_yearly_operation_hours,
        stored_power_daily_kWh,
    ):

        self.inp = {
            "Electrolysis Using Stored Power": {
                "Fraction of stored power used for electrolysis": {
                    "Value": fraction_stored_power_for_electrolysis
                }
            },
            "Electrolyzer": {
                "Nominal Power (kW)": {"Value": electrolyzer_nominal_power_kW},
                "Power requirement increase per year": {
                    "Value": electrolyzer_power_increase_per_year
                },
                "Minimum capacity": {"Value": electrolyzer_min_capacity},
                "Conversion efficiency (kg H2/kWh)": {
                    "Value": electrolyzer_conversion_efficiency
                },
                "Replacement time (h)": {"Value": electrolyzer_replacement_time_h},
                "H2 Production (yearly, kg)": {
                    "Value": electrolyzer_yearly_H2_production_kg,
                    "Processed": "Yes"
                },
                "Yearly Operation Data": {
                    "Value": electrolyzer_yearly_operation_hours,
                    "Processed": "Yes"
                },
            },
            "Power Generation": {
                "Stored Power (daily, kWh)": {
                    "Value": stored_power_daily_kWh,
                    "Processed": "Yes"
                }
            },
        }

        self.operation_years = np.array(list(stored_power_daily_kWh.keys()), dtype=float)
        

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "fraction_stored_power_for_electrolysis": 0.8,
                "electrolyzer_nominal_power_kW": 500.0,
                "electrolyzer_power_increase_per_year": 0.02,
                "electrolyzer_min_capacity": 0.1,
                "electrolyzer_conversion_efficiency": 0.05,
                "electrolyzer_replacement_time_h": 4000.0,
                "electrolyzer_yearly_H2_production_kg": np.array([0.0, 2.0]),
                "electrolyzer_yearly_operation_hours": np.array(
                    [[2026, 3.0, 0], [2027, 4.0, 0]]
                ),
                "stored_power_daily_kWh": {
                    2026: np.array([1000.0, 1200.0, 0]),
                    2027: np.array([900.0, 0, 700.0]),
                },
            },
            "expected": {
                "power_consumption_kWh": np.array([1760.0, 1280.0]),
                "replacement_frequency": 2.0,
                "new_h2_production_kg": np.array([3.3153904527033626e-16, 2.0000000000000004]),
            },
        }
    ],
)
def test_stored_power_electrolysis_plugin(case):
    """Test Stored_Power_Electrolysis_Plugin using variable-value inputs."""

    # Create DummyDCF
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Stored_Power_Electrolysis_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.power_consumption_kWh,
        expected["power_consumption_kWh"],
        rtol=tolerance,
        atol=tolerance,
    )
    
    assert plugin.replacement_frequency == pytest.approx(
        expected["replacement_frequency"],
        abs=tolerance,
    )

    np.testing.assert_allclose(
        plugin.new_h2_production_kg,
        expected["new_h2_production_kg"],
        rtol=tolerance,
        atol=tolerance,
    )
