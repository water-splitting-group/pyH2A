import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

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
    ):

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
        self.operation_years = list(available_power_hourly.keys())

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

    for year in dcf.operation_years:
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
