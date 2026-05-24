import pytest
import numpy as np
from pyH2A.Plugins.Stored_Power_Electrolysis_Plugin import Stored_Power_Electrolysis_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

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
        yearly_operation_data_year, 
        yearly_operation_data_production, 
        yearly_operation_data_duration, 
        stored_power_daily_kWh,
    ):

        self.inp = {
            "Electrolysis Using Stored Power": {
                "Fraction of stored power used for electrolysis": {
                    "Value" : fraction_stored_power_for_electrolysis, 
                    "Unit" : "-"
                }
            },
            "Electrolyzer": {
                "Nominal power": {
                    "Value": electrolyzer_nominal_power_kW, 
                    "Unit" : "kW"
                    },
                "Power requirement increase per year": {
                    "Value": electrolyzer_power_increase_per_year, 
                    "Unit" : "-"
                    },
                "Minimum capacity": {
                    "Value": electrolyzer_min_capacity, 
                    "Unit" : "-"
                    },
                "Hydrogen yield per unit energy": {
                    "Value": electrolyzer_conversion_efficiency,
                    "Unit" : "kg/kWh"
                    },
                "Replacement time": {
                    "Value": electrolyzer_replacement_time_h, 
                    "Unit" : "h"},
                "H2 production (yearly)": {
                    "Value": electrolyzer_yearly_H2_production_kg, 
                    "Unit" : "kg / year",
                    "Processed": "Yes"
                    },
                "Yearly operation data": {
                    "Year_Value" : yearly_operation_data_year, 
                    "Year_Unit" : "-", 
                    "Production_Value" : yearly_operation_data_production,
                    "Production_Unit" : "kg", 
                    "Duration_Value": yearly_operation_data_duration, 
                    "Duration_Unit" : "h", 
                    "Processed": "Yes"
                    },
            },
            "Power Generation": {
                "Stored energy (daily)": {
                    "Value": stored_power_daily_kWh, 
                    "Unit" : "kWh",
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
                "electrolyzer_yearly_H2_production_kg": np.array([1.0, 8.0]),
                "yearly_operation_data_year": np.array([2026, 2027]),
                "yearly_operation_data_production": np.array([1., 8.]),
                "yearly_operation_data_duration": np.array([10., 80.]),             
                "stored_power_daily_kWh": {
                    2026: np.array([1000.0, 1200.0, 0]),
                    2027: np.array([900.0, 0, 700.0]),
                },
            },
            "expected": {
                "energy_consumption": Quantity(np.array([1760.0, 1280.0]), "kWh"),
                "replacement_frequency": Quantity(2.0, "year"),
                "new_h2_production": Quantity(np.array([1.0, 8.0]), "kg/year"),
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
        plugin.energy_consumption.unit['J'],
        expected["energy_consumption"].unit['J'],
        rtol=tolerance,
        atol=tolerance,
    )
    
    assert plugin.replacement_frequency.unit['s'] == pytest.approx(
        expected["replacement_frequency"].unit['s'],
        abs=tolerance,
    )
    
    np.testing.assert_allclose(
        plugin.new_h2_production.unit['kg/s'],
        expected["new_h2_production"].unit['kg/s'],
        rtol=tolerance,
        atol=tolerance,
    )
