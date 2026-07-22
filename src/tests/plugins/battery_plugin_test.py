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
        energy_density=None,
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

        # "Energy density" is an optional input, only added to dcf.inp when provided,
        # matching how a real input file would omit an unused optional row.
        if energy_density is not None:
            self.inp["Battery"]["Energy density"] = {
                "Value": energy_density,
                "Unit": "kWh/kg",
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
                "loss_of_capacity": 0.01,
                "round_trip_efficiency": 1.0,
                "energy_density": None,
            },
           "expected": {
                "yearly_recovered_energy": {
                    5: Quantity(np.array([6.086336319359999, 5.2, 6.086336319359999, 6.086336319359999]), "kWh"),
                    6: Quantity(np.array([6.0254729561664, 6.0254729561664, 6.0254729561664, 6.0254729561664]), "kWh"),
                },
                "yearly_unstored_energy": {
                    5: Quantity(np.array([4.11366368064, 0.0, 6.11366368064, 6.11366368064]), "kWh"),
                    6: Quantity(np.array([16.1745270438336, 0.17452704383360015, 2.1745270438335993, 3.1745270438335993]), "kWh"),
                },
                "battery_mass": None,
            },
        },
        {
            "input": {
                "operation_years_relative": {
                    "Operation years relative": np.array([2027, 2028])
                },
                "available_power": {
                    2027: np.array([10.2, 5.2, 12.2, 12.2]),
                    2028: np.array([22.2, 6.2, 8.2, 9.2]),
                },
                "design_capacity": 800000.0,
                "lowest_discharge_level": 0.20,
                "loss_of_capacity": 0.01,
                "round_trip_efficiency": 1.0,
                "energy_density": 0.2,
            },
           "expected": {
                "yearly_recovered_energy": {
                    2027: Quantity(np.array([0.0009093256112687591, 0.0009093256112687591, 0.0009093256112687591, 0.0009093256112687591]), "kWh"),
                    2028: Quantity(np.array([0.0009002323551560716, 0.0009002323551560716, 0.0009002323551560716, 0.0009002323551560716]), "kWh"),
                },
                "yearly_unstored_energy": {
                    2027: Quantity(np.array([10.199090674388732, 5.1990906743887315, 12.199090674388732, 12.199090674388732]), "kWh"),
                    2028: Quantity(np.array([22.199099767644846, 6.199099767644844, 8.199099767644842, 9.199099767644842]), "kWh"),
                },
                "battery_mass": Quantity(4_000_000.0, "kg"),
            },
        },
    ],
    ids=[
        "Realistic case - Battery Plugin",
        "Realistic case - Battery Plugin with energy density (mass calculated)",
    ]
)
def test_battery_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct daily stored/unstored power,
    as well as installed battery mass when energy density is provided."""

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

    if expected["battery_mass"] is None:
        # No energy density provided: battery mass should not be calculated.
        assert not hasattr(plugin, "battery_mass")
    else:
        np.testing.assert_allclose(
            plugin.battery_mass.unit["kg"],
            expected["battery_mass"].unit["kg"],
            rtol=1e-5,
            atol=1e-9,
        )


def test_battery_plugin_zero_energy_density_raises():
    """Battery mass calculation must raise when energy density is zero, to avoid division by zero."""

    dcf = DummyDCF(
        operation_years_relative={"Operation years relative": np.array([2027])},
        available_power={2027: np.array([10.2, 5.2, 12.2, 12.2])},
        design_capacity=800000.0,
        lowest_discharge_level=0.20,
        loss_of_capacity=0.01,
        round_trip_efficiency=1.0,
        energy_density=0.0,
    )

    with pytest.raises(ValueError):
        Battery_Plugin(dcf, print_info=False)