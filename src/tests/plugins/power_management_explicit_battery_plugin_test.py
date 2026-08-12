import pytest
import numpy as np
from pyH2A.Plugins.Power_Management_Explicit_Battery_Plugin import Power_Management_Explicit_Battery_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit



class DummyDCF:
    """Minimal DCF object for Power_Management_Explicit_Battery_Plugin testing with configurable inputs."""

    def __init__(
        self,
        operation_years_ones,
        available_hourly,
        total_yearly_generation,
        power_consumption,
        main_consumption_per_year,
        unsatisfied_demand,
        grid_cost,
    ):

        self.functional_unit = resolve_functional_unit('kWh')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_ones,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },               
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": available_hourly,
                    "Unit": "kWh",
                    "Processed": "Yes",
                },
                "Total yearly power generation": {
                    "Value": total_yearly_generation,
                    "Unit": "kWh",
                    "Processed": "Yes",
                },                
            },
            "Power Consumption": {
                "Test consumer": {
                    "Value": power_consumption["value"],
                    "Unit": "kWh",
                    "Processed": "Yes",
                },
            },
            "Main Consumer": {
                "Consumption per year": {
                    "Value": main_consumption_per_year,
                    "Unit": "kWh",
                },
            },            
            "Hourly Consumer Profile": {
                "Unsatisfied demand": {
                    "Value": unsatisfied_demand,
                    "Unit": "kWh",
                    "Processed": "Yes",
                },
            },            
            "Grid Electricity": {
                "Cost": {
                    "Value": grid_cost,
                    "Unit": "USD / kWh",
                }
            },
        }

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_ones": {"Operation years ones": np.ones(2)},                   
                "available_hourly": {
                    0: np.array([9.0, 12.0, 11.0]),
                    1: np.array([6.0, 4.0, 6.0]),
                },
                "total_yearly_generation":np.array([1000., 800]),
                "power_consumption": {
                    "value": np.array([20., 20]),
                },
                "main_consumption_per_year":np.array([450, 450.]),
                "unsatisfied_demand": {
                    0: np.array([1, 0, 0]),
                    1: np.array([0, 0, 1.0]),
                },                
                "grid_cost": 3.14159,
             
            },
            "expected": {
                "remaining_available": Quantity(np.array([12., 0.]), 'kWh'),
                "production_oversizing": Quantity(1.9148936170212767, '-'),
                "total_unfulfilled": Quantity(np.array([1.0, 5.0]), 'kWh'),
                "electricity_cost": Quantity(np.array([3.14159, 15.70795]), 'USD'),
            },
        },
    ],
)
def test_power_management_explicit_battery_plugin(case):
    """Test Power_Management_Explicit_Battery_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Power_Management_Explicit_Battery_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.remaining_available.unit['kWh'],
        expected["remaining_available"].unit['kWh'],
        rtol=tolerance,
        atol=tolerance,
    )

    assert plugin.production_oversizing.unit['-'] == pytest.approx(
        expected["production_oversizing"].unit['-'],
        abs=tolerance,
    )

    np.testing.assert_allclose(
        plugin.total_unfulfilled.unit['J'],
        expected["total_unfulfilled"].unit['J'],
        rtol=tolerance,
        atol=tolerance,
    )

    np.testing.assert_allclose(
        plugin.electricity_cost.unit['USD'],
        expected["electricity_cost"].unit['USD'],
        rtol=tolerance,
        atol=tolerance,
    )
    

