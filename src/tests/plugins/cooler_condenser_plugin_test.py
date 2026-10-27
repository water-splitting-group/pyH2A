import pytest
from pyH2A.Plugins.Cooler_Condenser_Plugin import Cooler_Condenser_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts
import numpy as np


class DummyDCF:
    """DCF object for Cooler_Condenser_Plugin with configurable inputs."""

    def __init__(
        self, relative_years, cold_inlet_temperature, cold_outlet_temperature, hot_outlet_temperature, heat_transfer_coefficient, material_weight_per_area, capacity_factor,temperature, pressure, specific_enthalpy, mass_fraction, hourly_mass_flow
    ):

        self.functional_unit = resolve_functional_unit('kg[H2]')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {'Operation years relative': relative_years},
                    "Unit": "-"
                },               
            },                  
            "Cooler Condenser": {
                "Cold inlet temperature": {
                    "Value": cold_inlet_temperature,
                    "Unit": "degC"
                }, 
                "Cold outlet temperature": {
                    "Value": cold_outlet_temperature,
                    "Unit": "degC"
                },  
                "Hot outlet temperature": {
                    "Value": hot_outlet_temperature,
                    "Unit": "degC"
                },  
                "Heat transfer coefficient": {
                    "Value": heat_transfer_coefficient,
                    "Unit": "W/m2/delta_K"
                },      
                "Material weight per area": {
                    "Value": material_weight_per_area,
                    "Unit": "kg/m2"
                },                                                                    
            },      
            "Technical Operating Parameters and Specifications": {
                "Operating capacity factor": {
                    "Value": capacity_factor,
                    "Unit": "-"
                }, 
            },               
            "Main Stream": {
                "Temperature": {
                    "Value": temperature,
                    "Unit": "degC"
                },
                "Pressure": {
                    "Value": pressure,
                    "Unit": "Pa"
                },
                "Specific enthalpy": {
                    "Value": specific_enthalpy,
                    "Unit": "J/kg"
                },
                "Mass fraction": {
                    "Value": mass_fraction,
                    "Unit": "-"
                },
                "Mass flow (hourly)": {
                    "Value": hourly_mass_flow,
                    "Unit": "kg"
                },                                                                                               
                                
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "relative_years":  np.array([0, 1]),
                "cold_inlet_temperature": 20,
                "cold_outlet_temperature": 35,
                "hot_outlet_temperature": 40,
                "heat_transfer_coefficient": 300,    
                "material_weight_per_area": 34,   
                "capacity_factor": 0.9,         
                "temperature": {0:np.array([60, 60]), 
                                1:np.array([60, 60]) },
                "pressure": 1.01315e5,
                "specific_enthalpy":{0:np.array([-3529060.931274817, -3529060.931274817]), 
                                1:np.array([-3529060.931274817, -3529060.931274817])},
                "mass_fraction": {0:{'H2': np.array([0.0818433531892011, 0.0818433531892011]), 'O2': np.array([0.6495098252351335, 0.6495098252351335]), 'H2O': np.array([0.2686468215756655, 0.2686468215756655])},
                                  1:{'H2': np.array([0.0818433531892011, 0.0818433531892011]), 'O2': np.array([0.6495098252351335, 0.6495098252351335]), 'H2O': np.array([0.2686468215756655, 0.2686468215756655])}
                                },
                "hourly_mass_flow": {0: np.arange(0, 2), 
                                     1: np.arange(2,4)},                
            },
            "expected": {
                "hourly_heat_duty": {0: Quantity(np.array([0, 483312.77924424503]), 'J'),
                                     1: Quantity(np.array([966625.5584884901, 1449938.337732736]), 'J')},
                "yearly_heat_duty": Quantity(np.array([434981.5013198205, 2174907.5065991036]), 'J'),
                "sizing_heat_duty": Quantity(402.7606493702045, 'W'),
                "heat_exchange_area": Quantity(0.05991562775338979, 'm2'),
                "peak_condensed_water_flowrate": Quantity(0.00015206853795844482, 'kg/s'),
                "yearly_condensed_water_mass": Quantity(np.array([0.16423402099512038, 0.8211701049756019]), 'kg'),
                "sizing_coolant_flowrate": Quantity(0.006414407538942578, 'kg/s'),
                "hourly_coolant_mass":  {0: Quantity(np.array([0., 7.697289046731097 ]), 'kg'), 
                                      1: Quantity(np.array([15.394578093462194, 23.091867140193287]), 'kg')},  
                "yearly_coolant_mass": Quantity(np.array([6.927560142057979, 34.637800710289916 ]), 'kg'),
                "total_coolant_mass": Quantity(41.565360852347894, 'kg'),
                "outlet_temperature": {0:Quantity(np.array([40.0, 40]), 'degC'),
                                       1:Quantity(np.array([40.0, 40]), 'degC')},
                "outlet_enthalpy": {0:Quantity(np.array([-1380293.484041347, -1380293.484041347]), 'J/kg'),
                                    1:Quantity(np.array([-1380293.484041347, -1380293.484041347]), 'J/kg')},
                "outlet_mass_fraction": {0:{'H2': Quantity(np.array([0.10011201927262867, 0.10011201927262867]), '-'), 'O2': Quantity(np.array([0.7944901767573346, 0.7944901767573346]), '-'), 'H2O': Quantity(np.array([0.10539780397003685, 0.10539780397003685]), '-')},
                                         1:{'H2': Quantity(np.array([0.10011201927262867, 0.10011201927262867]), '-'), 'O2': Quantity(np.array([0.7944901767573346, 0.7944901767573346]), '-'), 'H2O': Quantity(np.array([0.10539780397003685, 0.10539780397003685]), '-')}
                                        },
                "hourly_mass_flow":  {0: Quantity(np.array([0, 0.8175177544498663]), 'kg'), 
                                      1: Quantity(np.array([1.6350355088997326, 2.4525532633495986 ]), 'kg')},                                      
            },
        },
    ],
    ids=[
        "Realistic case - Post-baggie condensation"
    ]
)
def test_cooler_condenser_plugin(case):
    """Check Cooler_Condenser_Plugin calculates compresison work correctly."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Cooler_Condenser_Plugin(dcf, print_info=False)
    tol = 1e-12
    check_dicts(plugin.hourly_heat_duty, case["expected"]["hourly_heat_duty"])
    np.testing.assert_allclose(plugin.yearly_heat_duty.base_value,case["expected"]["yearly_heat_duty"].base_value,rtol=tol,atol=tol,)        
    assert plugin.sizing_heat_duty.base_value == case["expected"]["sizing_heat_duty"].base_value
    assert plugin.heat_exchange_area.base_value == case["expected"]["heat_exchange_area"].base_value
    assert plugin.peak_condensed_water_flowrate.base_value == case["expected"]["peak_condensed_water_flowrate"].base_value
    np.testing.assert_allclose(plugin.yearly_condensed_water_mass.base_value,case["expected"]["yearly_condensed_water_mass"].base_value,rtol=tol,atol=tol,)        
    assert plugin.sizing_coolant_flowrate.base_value == case["expected"]["sizing_coolant_flowrate"].base_value
    check_dicts(plugin.hourly_coolant_mass, case["expected"]["hourly_coolant_mass"])
    np.testing.assert_allclose(plugin.yearly_coolant_mass.base_value,case["expected"]["yearly_coolant_mass"].base_value,rtol=tol,atol=tol,)  
    assert plugin.total_coolant_mass.base_value == case["expected"]["total_coolant_mass"].base_value     
    check_dicts(plugin.outlet_temperature, case["expected"]["outlet_temperature"])
    check_dicts(plugin.outlet_enthalpy, case["expected"]["outlet_enthalpy"])
    check_dicts(plugin.outlet_mass_fraction, case["expected"]["outlet_mass_fraction"])
    check_dicts(plugin.hourly_mass_flow, case["expected"]["hourly_mass_flow"])            
