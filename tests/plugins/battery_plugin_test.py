import pytest
from pyH2A.Plugins.Battery_Plugin import Battery_Plugin
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """DCF object for Battery_plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        available_power,
        design_capacity,
        lowest_discharge_level,
        loss_of_capacity,
        round_trip_efficiency,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },            
            "Power Generation": {
                "Available energy (daily)": {
                    "Value": available_power,
                    "Unit": "kWh",   
                    "Processed": "Yes",
                },
            },
            "Battery": {
               "Design capacity": {
                    "Value": design_capacity,
                    "Unit": "kWh"
                },
                "Lowest discharge level": {
                    "Value": lowest_discharge_level,
                    "Unit": "-"
                },
                "Capacity loss per year": {
                    "Value": loss_of_capacity,
                    "Unit": "-"
                },
                "Round trip efficiency": {
                    "Value": round_trip_efficiency,
                    "Unit": "-"
                },
            }
        }
        self.operation_years = list(available_power.keys())


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {
                    # in the plugin logic, years are relative to startup year, not calendar year
                    'Operation years relative': np.arange(5, 7) 
                },                 
                "available_power": {
                    5: np.array([10.2, 5.2, 12.2, 12.2]),
                    6: np.array([22.2, 6.2, 8.2, 9.2]),
                },
                "design_capacity": 8.0,
                "lowest_discharge_level": 0.20,
                "loss_of_capacity": 0.02,
                "round_trip_efficiency": 0.95,
            },
           "expected": {
                "yearly_recovered_energy": {
                    5: Quantity(np.array([5.495838444544, 4.94, 5.495838444544, 5.495838444544]), "kWh"),
                    6: Quantity(np.array([5.385921675653119, 5.385921675653119, 5.385921675653119, 5.385921675653119]), "kWh"),
                },
                "yearly_unstored_energy": {
                    5: Quantity(np.array([4.414906900479999 , 0., 6.414906900479999 , 6.414906900479999 ]), "kWh"),
                    6: Quantity(np.array([16.5306087624704 , 0.5306087624704006, 2.5306087624703997 , 3.5306087624703997]), "kWh"),
                },
            },
        }
    ],
    ids=[
        "Realistic case - Battery Plugin",
    ]
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
            plugin.yearly_recovered_energy[year].unit["kWh"],
            expected["yearly_recovered_energy"][year].unit["kWh"],
            rtol=1e-12,
            atol=1e-12,
        )

        np.testing.assert_allclose(
            plugin.yearly_unstored_energy[year].unit["kWh"],
            expected["yearly_unstored_energy"][year].unit["kWh"],
            rtol=1e-12,
            atol=1e-12,
        )
