import pytest
from pyH2A.Plugins.Cooler_Condenser_Plugin import Cooler_Condenser_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Cooler_Condenser_Plugin with configurable inputs."""

    def __init__(
        self, cold_inlet_temperature, cold_outlet_temperature, hot_outlet_temperature, heat_transfer_coefficient, material_weight_per_area, capacity_factor,temperature, pressure, specific_enthalpy, mass_fraction, mass_flowrate, peak_flowrate
    ):

        self.functional_unit = resolve_functional_unit('kg')

        self.inp = {
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
                "Design mass flowrate": {
                    "Value": mass_flowrate,
                    "Unit": "kg/s"
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
                "mass_flowrate": 0.1571147294829186, 
                "peak_flowrate": 0.2

            },
            "expected": {
                "sizing_heat_duty": Quantity(96662.55584884912, 'W'),
                "heat_exchange_area": Quantity(14.379750660813556, 'm2'),
                "peak_condensed_water_flowrate": Quantity(0.03649644911002675, 'kg/s'),
                "yearly_condensed_water_mass": Quantity(813741.8181031193, 'kg'),
                "max_coolant_flowrate": Quantity(1.5394578093462195, 'kg/s'),
                "yearly_coolant_mass": Quantity(34324467.91998389, 'kg'),
                "outlet_temperature": Quantity(40.0, 'degC'),
                "outlet_enthalpy": Quantity(-1380293.484041347, 'J/kg'),
                "outlet_mass_fraction": {'H2': Quantity(0.10011201927262867, '-'), 'O2': Quantity(0.7944901767573346, '-'), 'H2O': Quantity(0.10539780397003685, '-')},
                "outlet_mass_flowrate": Quantity(0.12844408083787381, 'kg/s'),    
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

    assert plugin.sizing_heat_duty.base_value == case["expected"]["sizing_heat_duty"].base_value
    assert plugin.heat_exchange_area.base_value == case["expected"]["heat_exchange_area"].base_value
    assert plugin.peak_condensed_water_flowrate.base_value == case["expected"]["peak_condensed_water_flowrate"].base_value
    assert plugin.yearly_condensed_water_mass.base_value == case["expected"]["yearly_condensed_water_mass"].base_value
    assert plugin.max_coolant_flowrate.base_value == case["expected"]["max_coolant_flowrate"].base_value
    assert plugin.yearly_coolant_mass.base_value == case["expected"]["yearly_coolant_mass"].base_value
    assert plugin.outlet_temperature.base_value == case["expected"]["outlet_temperature"].base_value
    assert plugin.outlet_enthalpy.base_value == case["expected"]["outlet_enthalpy"].base_value
    for species in case["expected"]["outlet_mass_fraction"].keys():
        assert plugin.outlet_mass_fraction[species].base_value == case["expected"]["outlet_mass_fraction"][species].base_value
    assert plugin.outlet_mass_flowrate.base_value == case["expected"]["outlet_mass_flowrate"].base_value
    assert plugin.peak_mass_flowrate.base_value == case["expected"]["peak_mass_flowrate"].base_value
