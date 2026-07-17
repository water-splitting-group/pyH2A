import pytest
import numpy as np
from pyH2A.Plugins.Power_Management_Plugin import Power_Management_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF object for Power_Management_Plugin testing with configurable inputs."""

    def __init__(
        self,
        operation_years_ones,
        available_daily,
        stored_daily,
        power_consumption,
        grid_cost,
    ):

        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_ones,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },               
            "Power Generation": {
                "Available energy (daily)": {
                    "Value": available_daily,
                    "Unit": "kWh",
                    "Processed": "Yes",
                },
                "Stored energy (daily)": {
                    "Value": stored_daily,
                    "Unit": "kWh",
                    "Processed": "Yes",
                },
            },
            "Power Consumption": {
                "Test consumer": {
                    "Value": power_consumption["value"],
                    "Type": power_consumption["type"],
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
                "available_daily": {
                    2026: np.array([12000000.0, 11000000.0, 13000000.0]),
                    2027: np.array([12200000.0, 11200000.0, 13200000.0]),
                },
                "stored_daily": {
                    2026: np.array([8000000.0, 8000000.0, 8000000.0]),
                    2027: np.array([7000000.0, 8700000.0, 8070000.0])
                },
                "power_consumption": {
                    "value": np.array([95000000.0]),
                    "type": "flexible"
                },
                "grid_cost": 100000.12,
                "operation_years_ones": {"Operation years ones": np.ones(3)},                
            },
            "expected": {
                "remaining_flexible": Quantity(np.array([0., 0.]), 'kWh'),
                "remaining_stored": Quantity(np.array([0.0, 0.0]), 'kWh'),
                "total_unfulfilled": Quantity(np.array([35000000.0, 34630000.0]), 'kWh'),
                "electricity_cost": Quantity(np.array([3.5000042e12, 3.4630041556e12]), 'USD'),
            },
        },
        {
            "input": {
                "available_daily": {
                    2026: np.array([12000000.0, 11000000.0, 13000000.0]),
                    2027: np.array([12000000.0, 11000000.0, 13000000.0]),
                },
                "stored_daily": {
                    2026: np.array([8000000.0, 8000000.0, 8000000.0]),
                    2027: np.array([8000000.0, 8000000.0, 8000000.0]),
                },
                "power_consumption": {
                    "value": np.array([25000.0]),
                    "type": "on_demand"
                },
                "grid_cost": 100000.12,
                "operation_years_ones": {"Operation years ones": np.ones(3)},
            },
            "expected": {
                "remaining_flexible": Quantity(np.array([36000000.0, 36000000.0]), 'kWh'),
                "remaining_stored": Quantity(np.array([23975000.0, 23975000.0]), 'kWh'),
                "total_unfulfilled": Quantity(np.array([0.0, 0.0]), 'kWh'),
                "electricity_cost": Quantity(np.array([0.0, 0.0]), 'USD'),
            },
        }
    ],
)
def test_power_management_plugin(case):
    """Test Power_Management_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Power_Management_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.remaining_flexible.unit['J'],
        expected["remaining_flexible"].unit['J'],
        rtol=tolerance,
        atol=tolerance,
    )

    np.testing.assert_allclose(
        plugin.remaining_stored.unit['J'],
        expected["remaining_stored"].unit['J'],
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
    

