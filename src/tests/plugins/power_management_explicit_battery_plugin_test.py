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
        power_consumption,
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
            },
            "Power Consumption": {
                "Test consumer": {
                    "Value": power_consumption["value"],
                    "Unit": "kWh",
                    "Processed": "Yes",
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
                "operation_years_ones": {"Operation years ones": np.ones(3)},                   
                "available_hourly": {
                    0: np.array([9.0, 12.0, 11.0]),
                    1: np.array([6.0, 4.0, 6.0]),
                },
                "power_consumption": {
                    "value": np.array([20.]),
                },
                "unsatisfied_demand": {
                    0: np.array([1, 0, 0]),
                    1: np.array([0, 0, 1.0]),
                },                
                "grid_cost": 3.14159,
             
            },
            "expected": {
                "remaining_available": Quantity(np.array([12., 0.]), 'kWh'),
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
        plugin.remaining_available.unit['J'],
        expected["remaining_available"].unit['J'],
        rtol=tolerance,
        atol=tolerance,
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
    

