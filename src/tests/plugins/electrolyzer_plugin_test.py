import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts

class DummyDCF:
    """Minimal DCF object for Electrolyzer_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        operating_capacity_factor,
        nominal_power,
        unit_nominal_power,
        power_increase,
        min_capacity,
        min_power_coeff,
        efficiency,
        replacement_time,
        available_power_hourly,
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
            "Technical Operating Parameters and Specifications": {
                "Operating capacity factor": {
                    "Value": operating_capacity_factor, 
                    "Unit": "-"
                },
            },              
            "Electrolyzer": {
                "Nominal power": {
                    "Value": nominal_power, 
                    "Unit": "kW"
                },
                "Unit nominal power": {
                    "Value": unit_nominal_power, 
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
                "Minimum operating power coefficient": {
                    "Value": min_power_coeff, 
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

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {
                    'Operation years relative': np.arange(0, 2) 
                },       
                "operating_capacity_factor": 0.9,
                "nominal_power": 5500.0,
                "unit_nominal_power": 2750,
                "power_increase": 0.003,
                "min_capacity": 0.10,
                "min_power_coeff": 2,
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
                "yearly_data_year": Quantity(np.array([0.0, 1.0]),'-'),
                "yearly_data_production": Quantity(np.array([2441.9999999999995, 2350.4249999999993]),'kg'),
                "yearly_data_duration": Quantity(np.array([24.0, 23.1]),'h'),   
                "yearly_data_missing_energy":  {
                    0: Quantity(
                            np.array(
                                [
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19800000000,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19800000000,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19800000000,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19800000000,
                                    0 ,
                                    0 ,
                                ]
                            ),
                            "J"
                    ),
                    1: Quantity(
                            np.array(
                                [
                                    1985939999.9999998,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19859399999.999996,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19859399999.999996,
                                    0,
                                    0 ,
                                    0,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    19859399999.999996,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                ]
                        ),
                        'J'
                    ),    
                },
                "yearly_h2_production": Quantity(np.array([2441.9999999999995, 2350.4249999999993]), 'kg'),
                "replacement_frequency": Quantity(2.0, 'year'),
                "number_of_units": Quantity(2, '-'),
                "number_of_stacks":Quantity(2, '-'),
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
                "gross_yearly_mass": Quantity(np.array([20224.13193607285, 19487.648174912134]), 'kg'), 
                "net_yearly_mass" : Quantity(np.array([19639.56696428571, 18903.083203124996]), 'kg'),
                "outlet_enthalpy": {0: Quantity(np.array([-2120556.428686637]*24), 'J/kg'), 
                                        1: Quantity(np.array([-2120556.428686637]*24), 'J/kg')}, 
                "outlet_mass_fraction_H2": {'first':Quantity(0.7899035612816574, '-'),
                                         'last':Quantity(0.7899035612816574, '-')
                                        },                                         
                "hourly_mass_flow": {'first': Quantity(128.81319313829349, 'kg'), 
                                        'last': Quantity(128.81319313829349, 'kg')},                
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

    check_dicts(plugin.yearly_data_missing_energy, case["expected"]["yearly_data_missing_energy"])

    np.testing.assert_allclose(
        plugin.yearly_h2_production.unit['kg'],
        expected["yearly_h2_production"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )
    assert plugin.replacement_frequency.unit['year'] == pytest.approx(
        expected["replacement_frequency"].unit['year'],
        abs=tolerance
    )
    assert plugin.number_of_units.unit['-'] == pytest.approx(
        expected["number_of_units"].unit['-'],
        abs=tolerance
    )
    assert plugin.number_of_stacks.unit['-'] == pytest.approx(
        expected["number_of_stacks"].unit['-'],
        abs=tolerance
    )    

    check_dicts(plugin.yearly_data_unused_energy, case["expected"]["yearly_data_unused_energy"])    
    check_dicts(plugin.yearly_data_unused_energy_daily, case["expected"]["yearly_data_unused_energy_daily"])    

    assert plugin.gross_yearly_mass.unit['kg'] == pytest.approx(
        expected["gross_yearly_mass"].unit['kg'],
        abs=tolerance
    )   
    assert plugin.net_yearly_mass.unit['kg'] == pytest.approx(
        expected["net_yearly_mass"].unit['kg'],
        abs=tolerance
    )   

    check_dicts(plugin.outlet_enthalpy, case["expected"]["outlet_enthalpy"])    

    assert plugin.outlet_mass_fraction[0]['H2'].unit["-"][0] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['first'].unit["-"], 
        abs=tolerance
    )        

    assert plugin.outlet_mass_fraction[1]['H2'].unit["-"][-1] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['last'].unit["-"], 
        abs=tolerance
    )  

    assert plugin.hourly_mass_flow[0].unit["kg"][0] == pytest.approx(
        expected["hourly_mass_flow"]['first'].unit["kg"], 
        abs=tolerance
    )        
    assert plugin.hourly_mass_flow[1].unit["kg"][-1] == pytest.approx(
        expected["hourly_mass_flow"]['last'].unit["kg"], 
        abs=tolerance
    )  