import pytest
from pyH2A.Plugins.Cooler_Condenser_Plugin import Cooler_Condenser_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts
import numpy as np


class DummyDCF:
    """DCF object for Cooler_Condenser_Plugin with configurable inputs."""

    def __init__(
        self, relative_years, cold_inlet_temperature, cold_outlet_temperature, hot_outlet_temperature, heat_transfer_coefficient, material_weight_per_area, capacity_factor,temperature, pressure, specific_enthalpy, mass_fraction, hourly_mass_flow, yearly_mass, peak_flowrate
    ):

        self.functional_unit = resolve_functional_unit('kg')

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
                "Design mass flow by year": {
                    "Value": yearly_mass,
                    "Unit": "kg"
                },  
                "Peak mass flowrate": {
                    "Value": peak_flowrate,
                    "Unit": "kg/s"
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
                "temperature": 60,
                "pressure": 1.01315e5,
                "specific_enthalpy": -3529060.931274817,
                "mass_fraction": {'H2': 0.0818433531892011, 'O2': 0.6495098252351335, 'H2O': 0.2686468215756655},
                "hourly_mass_flow": {0: np.arange(0, 2), 
                                     1: np.arange(2,4)},                
                "yearly_mass": np.array([0.1571147294829186*365*86400, 0.1571147294829186*2*365*86400]), 
                "peak_flowrate": 0.2

            },
            "expected": {
                "sizing_heat_duty": Quantity(96662.55584884912, 'W'),
                "heat_exchange_area": Quantity(14.379750660813556, 'm2'),
                "peak_condensed_water_flowrate": Quantity(0.03649644911002675, 'kg/s'),
                "yearly_condensed_water_mass": Quantity(np.array([813741.8181031193, 813741.8181031193*2]), 'kg'),
                "max_coolant_flowrate": Quantity(1.5394578093462195, 'kg/s'),
                "hourly_coolant_mass":  {0: Quantity(np.array([0., 7.697289046731097 ]), 'kg'), 
                                      1: Quantity(np.array([15.394578093462194, 23.091867140193287]), 'kg')},  
                "yearly_coolant_mass": Quantity(np.array([34324467.91998389, 34324467.91998389*2]), 'kg'),
                "hourly_pumping_energy":  {0: Quantity(np.array([69275.60142057987, 69275.60142057987]), 'J'), 
                                      1: Quantity(np.array([69275.60142057987, 69275.60142057987]), 'J')},  
                "yearly_pumping_energy":  Quantity(np.array([124696.08255704377 , 124696.08255704377 ]), 'kg'),                                        
                "outlet_temperature": Quantity(40.0, 'degC'),
                "outlet_enthalpy": Quantity(-1380293.484041347, 'J/kg'),
                "outlet_mass_fraction": {'H2': Quantity(0.10011201927262867, '-'), 'O2': Quantity(0.7944901767573346, '-'), 'H2O': Quantity(0.10539780397003685, '-')},
                "hourly_mass_flow":  {0: Quantity(np.array([0, 0.8175177544498663]), 'kg'), 
                                      1: Quantity(np.array([1.6350355088997326, 2.4525532633495986 ]), 'kg')},              
                "yearly_mass_flow": Quantity(np.array([0.12844408083787381*86400*365, 0.12844408083787381*2*365*86400]), 'kg'),    
                "peak_mass_flowrate": Quantity(0.16350355088997326, 'kg/s'),                            
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
    assert plugin.sizing_heat_duty.base_value == case["expected"]["sizing_heat_duty"].base_value
    assert plugin.heat_exchange_area.base_value == case["expected"]["heat_exchange_area"].base_value
    assert plugin.peak_condensed_water_flowrate.base_value == case["expected"]["peak_condensed_water_flowrate"].base_value
    np.testing.assert_allclose(plugin.yearly_condensed_water_mass.base_value,case["expected"]["yearly_condensed_water_mass"].base_value,rtol=tol,atol=tol,)        
    assert plugin.max_coolant_flowrate.base_value == case["expected"]["max_coolant_flowrate"].base_value
    check_dicts(plugin.hourly_coolant_mass, case["expected"]["hourly_coolant_mass"])
    np.testing.assert_allclose(plugin.yearly_coolant_mass.base_value,case["expected"]["yearly_coolant_mass"].base_value,rtol=tol,atol=tol,)        
    check_dicts(plugin.hourly_pumping_energy, case["expected"]["hourly_pumping_energy"])
    np.testing.assert_allclose(plugin.yearly_pumping_energy.base_value,case["expected"]["yearly_pumping_energy"].base_value,rtol=tol,atol=tol,)      
    assert plugin.outlet_temperature.base_value == case["expected"]["outlet_temperature"].base_value
    assert plugin.outlet_enthalpy.base_value == case["expected"]["outlet_enthalpy"].base_value
    check_dicts(plugin.outlet_mass_fraction, case["expected"]["outlet_mass_fraction"])
    check_dicts(plugin.hourly_mass_flow, case["expected"]["hourly_mass_flow"])            
    np.testing.assert_allclose(plugin.yearly_mass_flow.base_value,case["expected"]["yearly_mass_flow"].base_value,rtol=tol,atol=tol,)      
    assert plugin.peak_mass_flowrate.base_value == case["expected"]["peak_mass_flowrate"].base_value
