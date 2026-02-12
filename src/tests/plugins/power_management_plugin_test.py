import pytest
import numpy as np
from pyH2A.Plugins.Power_Management_Plugin import Power_Management_Plugin


class DummyDCF:
    """Minimal DCF object for Power_Management_Plugin testing with configurable inputs."""

    def __init__(
        self,
        available_daily,
        stored_daily,
        power_consumption,
        grid_cost,
        construction_time,
    ):

        self.inp = {
            "Power Generation": {
                "Available Power (daily, kWh)": {
                    "Value": available_daily,
                    "Processed": "Yes",
                },
                "Stored Power (daily, kWh)": {
                    "Value": stored_daily,
                    "Processed": "Yes",
                },
            },
            "Power Consumption": {
                "Test Consumer": {
                    "Value": power_consumption,
                    "Type": "flexible",
                    "Processed": "Yes",
                },
            },
            "Grid Electricity": {"Cost ($/kWh)": {"Value": grid_cost}},
            "Financial Input Values": {
                "construction time": {"Value": construction_time}
            },
        }

        self.operation_years = list(available_daily.keys())


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "available_daily": {
                    2026: np.array([12000000.0, 11000000.0, 13000000.0]),
                },
                "stored_daily": {
                    2026: np.array([8000000.0, 8000000.0, 8000000.0]),
                },
                "power_consumption": np.array([25000.0]),
                "grid_cost": 100000.12,
                "construction_time": 1,
            },
            "expected": {
                "remaining_flexible": np.array([35975000.0]),
                "remaining_stored": np.array([24000000.0]),
                "total_unfulfilled": np.array([0.0]),
                "electricity_cost": np.array([0.0, 0.0]),
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
        plugin.remaining_flexible,
        expected["remaining_flexible"],
        rtol=tolerance,
        atol=tolerance,
    )

    np.testing.assert_allclose(
        plugin.remaining_stored,
        expected["remaining_stored"],
        rtol=tolerance,
        atol=tolerance,
    )

    np.testing.assert_allclose(
        plugin.total_unfulfilled,
        expected["total_unfulfilled"],
        rtol=tolerance,
        atol=tolerance,
    )

    np.testing.assert_allclose(
        plugin.electricity_cost,
        expected["electricity_cost"],
        rtol=tolerance,
        atol=tolerance,
    )
