import pytest
from pyH2A.Plugins.Battery_Plugin import Battery_Plugin
import numpy as np


class DummyDCF:
    """DCF object for Battery_plugin with configurable inputs."""

    def __init__(
        self,
        available_power,
        design_capacity,
        lowest_discharge_level,
        loss_of_capacity,
        round_trip_efficiency,
    ):
        self.inp = {
            "Power Generation": {
                "Available Power (daily, kWh)": {
                    "Value": available_power,
                    "Processed": "Yes",
                }
            },
            "Battery": {
                "Design Capacity (kWh)": {"Value": design_capacity},
                "Lowest discharge level": {"Value": lowest_discharge_level},
                "Capacity loss per year": {"Value": loss_of_capacity},
                "Round trip efficiency": {"Value": round_trip_efficiency},
            },
        }
        self.operation_years = list(available_power.keys())


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "available_power": {
                    2027: np.array([10.2, 5.2, 12.2, 12.2]),
                    2028: np.array([22.2, 6.2, 8.2, 9.2]),
                },
                "design_capacity": 800000,
                "lowest_discharge_level": 0.20,
                "loss_of_capacity": 0.01,
                "round_trip_efficiency": 1,
            },
            "expected": {
                "yearly_recovered_power": {
                    2027: np.array([0.00090933, 0.00090933, 0.00090933, 0.00090933]),
                    2028: np.array([0.00090023, 0.00090023, 0.00090023, 0.00090023]),
                },
                "yearly_unstored_power": {
                    2027: np.array([10.19909067, 5.19909067, 12.19909067, 12.19909067]),
                    2028: np.array([22.19909977, 6.19909977, 8.19909977, 9.19909977]),
                },
            },
        }
    ],
)
def test_battery_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct daily stored/unstored power."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Battery_Plugin(dcf, print_info=False)
    expected = case["expected"]

    for year in dcf.operation_years:

        np.testing.assert_allclose(
            plugin.yearly_recovered_power[year],
            expected["yearly_recovered_power"][year],
            rtol=1e-5,  # slightly higher relative tolerance
            atol=1e-9,  # keep a small absolute tolerance
        )

        np.testing.assert_allclose(
            plugin.yearly_unstored_power[year],
            expected["yearly_unstored_power"][year],
            rtol=1e-5,
            atol=1e-9,
        )
