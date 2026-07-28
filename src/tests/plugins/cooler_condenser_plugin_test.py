import pytest
from pyH2A.Plugins.Cooler_Condenser_Plugin import Cooler_Condenser_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """DCF object for Cooler_Condenser_Plugin with configurable inputs."""

    def __init__(
        self, cold_inlet_temperature, cold_outlet_temperature, hot_outlet_temperature, heat_transfer_coefficient, material_weight_per_area, temperature, pressure, specific_enthalpy, mass_fraction, mass_flowrate
    ):
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
                "Mass flowrate": {
                    "Value": mass_flowrate,
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
                "temperature": 60,
                "pressure": 1.01315e5,
                "specific_enthalpy": -3529060.931274817,
                "mass_fraction": {'H2': 0.0818433531892011, 'O2': 0.6495098252351335, 'H2O': 0.2686468215756655},
                "mass_flowrate": 0.1571147294829186

            },
            "expected": {
                "heat_duty": Quantity(75935.5565665972, 'W'),
                "heat_exchange_area": Quantity(11.296353175527708, 'm2'),
                "coolant_flowrate": Quantity(1.2093574863289887, 'kg/s'),
                "outlet_temperature": Quantity(40.0, 'degC'),
                "outlet_enthalpy": Quantity(-1380293.484041347, 'J/kg'),
                "outlet_mass_fraction": {'H2': Quantity(0.10011201927262867, '-'), 'O2': Quantity(0.7944901767573346, '-'), 'H2O': Quantity(0.10539780397003685, '-')},
                "outlet_mass_flowrate": Quantity(0.12844408083787381, 'kg/s'),                                
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

    assert plugin.heat_duty.base_value == case["expected"]["heat_duty"].base_value
    assert plugin.heat_exchange_area.base_value == case["expected"]["heat_exchange_area"].base_value
    assert plugin.coolant_flowrate.base_value == case["expected"]["coolant_flowrate"].base_value
    assert plugin.outlet_temperature.base_value == case["expected"]["outlet_temperature"].base_value
    assert plugin.outlet_enthalpy.base_value == case["expected"]["outlet_enthalpy"].base_value
    for species in case["expected"]["outlet_mass_fraction"].keys():
        assert plugin.outlet_mass_fraction[species].base_value == case["expected"]["outlet_mass_fraction"][species].base_value
    assert plugin.outlet_mass_flowrate.base_value == case["expected"]["outlet_mass_flowrate"].base_value
