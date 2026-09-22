import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """Minimal DCF object for Electrolyzer_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        nominal_power,
        power_increase,
        min_capacity,
        efficiency,
        replacement_time,
        available_power_hourly,
        unit_power=None,
    ):

        self.functional_unit = resolve_functional_unit('kg[H2]')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },    
            "Electrolyzer": {
                "Nominal power": {
                    "Value": nominal_power, 
                    "Unit": "kW"
                },
                "Power requirement increase per year": {
                    "Value": power_increase, 
                    "Unit": "-"
                },
                "Minimum capacity": {
                    "Value": min_capacity, 
                    "Unit": "-"
                },
                "Hydrogen yield per unit energy": {
                    "Value": efficiency,
                    "Unit": "kg/kWh"
                },
                "Replacement time": {
                    "Value": replacement_time, 
                    "Unit": "h"},
            },
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": available_power_hourly,
                    "Unit": "kWh",
                    "Processed": "Yes",
                }
            },
        }

        # "Unit nominal power" is optional, so it is only added when provided,
        # in the same way as an input file would omit it.
        if unit_power is not None:
            self.inp["Electrolyzer"]["Unit nominal power"] = {
                "Value": unit_power,
                "Unit": "kW",
            }

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {
                    # in the plugin logic, years are relative to startup year, not calendar year
                    'Operation years relative': np.arange(0, 2) 
                },       
                "nominal_power": 5500.0,
                "power_increase": 0.003,
                "min_capacity": 0.10,
                "efficiency": 0.0185,
                "replacement_time": 80000.0,
                "available_power_hourly": {
                    0: np.array(
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
                    1: np.array(
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
                "h2_production": Quantity(np.array([2035.0, 2035.0]), 'kg'),
                "replacement_frequency": Quantity(2.0, 'year'),
                "yearly_data_year": Quantity(np.array([0.0, 1.0]),'-'),
                "yearly_data_production": Quantity(np.array([2035.0, 2035.0]),'kg'),
                "yearly_data_duration": Quantity(np.array([20.0, 20.0]),'h'),                                
                "yearly_data_unused_energy": {
                    0: Quantity(
                            np.array(
                                [
                                    199994500.2 ,
                                    200494500.2 ,
                                    201194500.2 ,
                                    201194500.2 ,
                                    0.0,
                                    200494500.2,
                                    201194500.2,
                                    201194500.2,
                                    200994500.2,
                                    200494500.2 ,
                                    201194500.2 ,
                                    201194500.2 ,
                                    200994500.2 ,
                                    0.0,
                                    201194500.2 ,
                                    201194500.2 ,
                                    200994500.2 ,
                                    0.0,
                                    201194500.2 ,
                                    201194500.2 ,
                                    200994500.2 ,
                                    0.0,
                                    201194500.2 ,
                                    201194500.2 ,
                                ]
                            ),
                            "kWh"
                    ),
                    1: Quantity(
                            np.array(
                                [
                                    0.0,
                                    200494483.7 ,
                                    201194483.7 ,
                                    201194483.7 ,
                                    200994483.7 ,
                                    0.0,
                                    201194483.7 ,
                                    201194483.7 ,
                                    200994483.7 ,
                                    200494483.7 ,
                                    201194483.7 ,
                                    0.0,
                                    200994483.7,
                                    206494483.7 ,
                                    201194483.7,
                                    201194483.7 ,
                                    200994483.7 ,
                                    207494483.7 ,
                                    201194483.7 ,
                                    0.0,
                                    200994483.7 ,
                                    208494483.7 ,
                                    201194483.7 ,
                                    201194483.7 ,
                                ]
                        ),
                        'kWh'
                    ),    
                },
                "yearly_data_unused_energy_daily": {
                    0: Quantity(np.array([4019790003.9999995]), 'kWh'),
                    1: Quantity(np.array([4040389673.9999995]), 'kWh'),
                },
                # Power demand is limiting in every operating hour: 20 h * 5500 kW * 1.003^year
                "electricity_consumption": Quantity(np.array([110000.0, 110330.0]), 'kWh'),
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
        plugin.h2_production.unit['kg'],
        expected["h2_production"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )
    
    assert plugin.replacement_frequency.unit['year'] == pytest.approx(
        expected["replacement_frequency"].unit['year'],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.yearly_data_year.unit['-'],
        expected["yearly_data_year"].unit['-'],
        rtol=tolerance,
        atol=tolerance,
    )
    np.testing.assert_allclose(
        plugin.yearly_data_production.unit['kg'],
        expected["yearly_data_production"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )
    np.testing.assert_allclose(
        plugin.yearly_data_duration.unit['s'],
        expected["yearly_data_duration"].unit['s'],
        rtol=tolerance,
        atol=tolerance,
    )

    for year in plugin.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
        np.testing.assert_allclose(
            plugin.yearly_data_unused_energy[year].unit['J'],
            expected["yearly_data_unused_energy"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )

        np.testing.assert_allclose(
            plugin.yearly_data_unused_energy_daily[year].unit['J'],
            expected["yearly_data_unused_energy_daily"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )

    np.testing.assert_allclose(
        plugin.electricity_consumption.unit['kWh'],
        expected["electricity_consumption"].unit['kWh'],
        rtol=tolerance,
    )

    # Without unit nominal power, no unit or stack counts are calculated (or inserted).
    assert not hasattr(plugin, "number_of_electrolyzers_required")
    assert not hasattr(plugin, "number_of_stacks_over_plant_life")
    assert "Number of electrolyzers required" not in dcf.inp["Electrolyzer"]
    assert "Number of stacks over plant life" not in dcf.inp["Electrolyzer"]


def test_electrolyzer_plugin_number_of_electrolyzers_and_stacks():
    """Check electricity consumption, number of electrolyzers and number of stacks over
    plant life, using inputs different from the realistic case and values derived by hand.

    Per year, the 1000 kW electrolyzer demands 1000 * 1.01^year kWh per hour. Of the hours
    with available energy (2000, 500 and 50 kWh, followed by 21 hours without energy), the
    first two exceed the minimum capacity of 10 %, while 50 kWh is below 10 % of the demand,
    so it is not used:

    - consumption: 1000 + 500, 1010 + 500 and 1020.1 + 500 kWh in years 0, 1 and 2,
    - H2 production: consumption * 0.02 kg/kWh / 1.01^year,
    - operating time: 2 h per year, 6 h in total, so a replacement time of 2.5 h
      leads to floor(6 / 2.5) = 2 replacements, i.e. one stack every 3 / (2 + 1) = 1 year,
    - 1000 kW / 250 kW = 4 electrolyzers, each with 1 initial and 2 replacement stacks.
    """

    available_energy = np.concatenate([[2000.0, 500.0, 50.0], np.zeros(21)])

    dcf = DummyDCF(
        operation_years_relative={"Operation years relative": np.arange(0, 3)},
        nominal_power=1000.0,
        power_increase=0.01,
        min_capacity=0.10,
        efficiency=0.02,
        replacement_time=2.5,
        available_power_hourly={year: available_energy for year in range(3)},
        unit_power=250.0,
    )

    plugin = Electrolyzer_Plugin(dcf, print_info=False)

    tolerance = 1e-12

    np.testing.assert_allclose(plugin.electricity_consumption.unit['kWh'],
                               [1500.0, 1510.0, 1520.1],
                               rtol=tolerance)
    np.testing.assert_allclose(plugin.h2_production.unit['kg'],
                               [1500.0 * 0.02, 1510.0 * 0.02 / 1.01, 1520.1 * 0.02 / 1.0201],
                               rtol=tolerance)
    np.testing.assert_allclose(plugin.yearly_data_unused_energy[2].unit['kWh'],
                               np.concatenate([[2000.0 - 1020.1, 0.0, 50.0], np.zeros(21)]),
                               rtol=tolerance)
    assert plugin.replacement_frequency.unit['year'] == pytest.approx(1.0, rel=tolerance)
    assert plugin.number_of_electrolyzers_required.unit['-'] == pytest.approx(4.0, rel=tolerance)
    assert plugin.number_of_stacks_over_plant_life.unit['-'] == pytest.approx(12.0, rel=tolerance)

    # Both counts are inserted into the Electrolyzer table for use by other plugins (e.g. LCA).
    assert dcf.inp["Electrolyzer"]["Number of electrolyzers required"]["Value"].unit['-'] == pytest.approx(4.0)
    assert dcf.inp["Electrolyzer"]["Number of stacks over plant life"]["Value"].unit['-'] == pytest.approx(12.0)
    np.testing.assert_allclose(dcf.inp["Electrolyzer"]["Electricity consumption (yearly)"]["Value"].unit['MJ'],
                               np.array([1500.0, 1510.0, 1520.1]) * 3.6,
                               rtol=tolerance)


def test_electrolyzer_plugin_zero_unit_power_raises():
    """A unit nominal power of zero would divide by zero, so it is rejected."""

    dcf = DummyDCF(
        operation_years_relative={"Operation years relative": np.arange(0, 1)},
        nominal_power=1000.0,
        power_increase=0.01,
        min_capacity=0.10,
        efficiency=0.02,
        replacement_time=2.5,
        available_power_hourly={0: np.concatenate([[2000.0, 500.0, 50.0], np.zeros(21)])},
        unit_power=0.0,
    )

    with pytest.raises(ValueError, match="unit nominal power must be greater than zero"):
        Electrolyzer_Plugin(dcf, print_info=False)
