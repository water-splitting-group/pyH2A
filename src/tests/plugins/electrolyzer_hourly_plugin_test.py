import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Hourly_Plugin import Electrolyzer_Hourly_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts

class DummyDCF:
    """Minimal DCF object for Electrolyzer_Hourly_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        nominal_power,
        power_increase,
        min_capacity,
        min_coeff,
        efficiency,
        replacement_time,
        available_power_hourly,
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
                "Minimum operating power coefficient": {
                    "Value": min_coeff, 
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
                "nominal_power": 5500.0,
                "power_increase": 0.003,
                "min_capacity": 0.10,
                "min_coeff": 0.4,
                "efficiency": 0.0185,
                "replacement_time": 80000.0,
                "available_power_hourly": {
                    0: np.array(
                        [
                            8000,
                            7500,
                            7000,
                            6500,
                            0.0,
                            6000,
                            6500,
                            7000,
                            7500,
                            8000,
                            7000,
                            6000,
                            5000,
                            0.0,
                            7500,
                            7000,
                            6500,
                            0.0,
                            7500,
                            7000,
                            6500,
                            0.0,
                            7500,
                            7000,
                        ]
                    ),
                    1: np.array(
                        [
                            0.0,
                            8000,
                            7500,
                            7000,
                            6500,
                            0.0,
                            6000,
                            6500,
                            7000,
                            7500,
                            8000,
                            0.0,
                            6500,
                            7000,
                            7500,
                            8000,
                            7000,
                            6000,
                            5000,
                            0.0,
                            6000,
                            6500,
                            7000,
                            7500,
                        ]
                    ),
                },
            },
            "expected": {
                "h2_production": Quantity(np.array([2066.635, 2066.17333001]), 'kg'),
                "replacement_frequency": Quantity(2.0, 'year'),
                "yearly_data_year": Quantity(np.array([0.0, 1.0]),'-'),
                "yearly_data_production": Quantity(np.array([2066.635, 2066.17333001]),'kg'),
                "yearly_data_missing_energy": {
                    0: Quantity(
                            np.array(
                                [
                                    0 ,
                                    0 ,
                                    0 ,
                                    0, 
                                    560,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0 ,
                                    0,
                                    550,
                                    0 ,
                                    0 ,
                                    0,
                                    550,
                                    0 ,
                                    0 ,
                                    0 ,
                                    550,
                                    0 ,
                                    0 ,
                                ]
                            ),
                            "kWh"
                    ),
                    1: Quantity(
                            np.array(
                                [
                                    551.65,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    551.65,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0,
                                    551.65,
                                    0,
                                    0 ,
                                    0,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                    551.65,
                                    0 ,
                                    0 ,
                                    0 ,
                                    0 ,
                                ]
                        ),
                        'kWh'
                    ),    
                },
                "yearly_data_duration": Quantity(np.array([73119.27272727274, 73102.93845735521]),'s'),                                
                "yearly_data_unused_energy": {
                    0: Quantity(
                            np.array(
                                [
                                    2500 ,
                                    2000 ,
                                    1500 ,
                                    1000, 
                                    0.0,
                                    500,
                                    1000,
                                    1500,
                                    2000,
                                    2500,
                                    1500,
                                    500 ,
                                    0,
                                    0,
                                    2000 ,
                                    1500 ,
                                    1000,
                                    0.0,
                                    2000 ,
                                    1500 ,
                                    1000 ,
                                    0.0,
                                    2000 ,
                                    1500 ,
                                ]
                            ),
                            "kWh"
                    ),
                    1: Quantity(
                            np.array(
                                [
                                    0.0,
                                    2483.5 ,
                                    1983.5 ,
                                    1483.50 ,
                                    983.50 ,
                                    0.0,
                                    483.5 ,
                                    983.5 ,
                                    1483.50 ,
                                    1983.5 ,
                                    2483.5,
                                    0.0,
                                    983.50,
                                    1483.5 ,
                                    1983.5,
                                    2483.5 ,
                                    1483.5 ,
                                    483.5 ,
                                    0 ,
                                    0,
                                    483.5 ,
                                    983.5 ,
                                    1483.5 ,
                                    1983.5 ,
                                ]
                        ),
                        'kWh'
                    ),    
                },
                "yearly_data_unused_energy_daily": {
                    0: Quantity(np.array([29000.0]), 'kWh'),
                    1: Quantity(np.array([28186.5]), 'kWh'),
                },
                "outlet_enthalpy": Quantity(-2120556.428686637, 'J/kg'),   
                "outlet_mass_fraction":{'H2': Quantity(0.7899035612816574, '-'),
                                        'H2O': Quantity(1-0.7899035612816574, '-'),
                                         },
                "yearly_mass_flow":Quantity(np.array([2616.3130555415933, 2615.728591801133]), 'kg'), 
                "peak_mass_flowrate": Quantity(3091.516635319044, 'kg/day'), 
                "hourly_mass_flow": {
                    0: Quantity(
                            np.array(
                                [
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    13.115525119535336, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    117.10290285299409, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349,                                                                                                                                                                                     
                                ]
                            ),
                            "kg"
                    ),
                    1: Quantity(
                            np.array(
                                [
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    116.75264491823938, 
                                    12.88131931382935, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349, 
                                    128.81319313829349,                                                                                                                                                                                     
                                ]
                        ),
                        'kg'
                    ),    
                },                
            },
        },
    ],
)
def test_electrolyzer_hourly_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Electrolyzer_Hourly_Plugin(dcf, print_info=False)
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

    check_dicts(plugin.yearly_data_missing_energy, case["expected"]["yearly_data_missing_energy"])

    np.testing.assert_allclose(
        plugin.yearly_data_duration.unit['s'],
        expected["yearly_data_duration"].unit['s'],
        rtol=tolerance,
        atol=tolerance,
    )

    check_dicts(plugin.yearly_data_unused_energy, case["expected"]["yearly_data_unused_energy"])


    check_dicts(plugin.yearly_data_unused_energy_daily, case["expected"]["yearly_data_unused_energy_daily"])

    assert plugin.outlet_enthalpy.unit["J/kg"] == pytest.approx(
        expected["outlet_enthalpy"].unit["J/kg"], 
        abs=tolerance
    )

    check_dicts(plugin.outlet_mass_fraction, case["expected"]["outlet_mass_fraction"])

    np.testing.assert_allclose(plugin.yearly_mass_flow.unit["kg"],case["expected"]["yearly_mass_flow"].unit["kg"],rtol=tolerance,atol=tolerance,)        

    assert plugin.peak_mass_flowrate.unit["kg/day"] == pytest.approx(
        expected["peak_mass_flowrate"].unit["kg/day"], 
        abs=tolerance
    )        

    check_dicts(plugin.hourly_mass_flow, case["expected"]["hourly_mass_flow"])         
