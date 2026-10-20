import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from pyH2A.Plugins.RFB_Plugin import RFB_Plugin


class DummyDCF:
    """DCF object for RFB_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_ones,
        Battery_power,
        Storage_capacity, 
        areal_energy_capacity,
        cell_stack_area,
        current_density, 
        discharge_voltage, 
        lifetime,
        Energy_density, 
        electrolyte_replacement, 
        electrolyte_regeneration,
        electrolyte_density,
        pump_lifetime,
        electrolyte_gwp, 
        electrolyte_energy, 
        electrolyte_toxicity, 
        electrolyte_resource_use,
    ):
        
        self.functional_unit = resolve_functional_unit('kWh[electricity]')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_ones,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },            
            "Battery": {
                "Power": {"Value": Battery_power, "Unit" : "MW"},
                "Gross capacity": {"Value": Storage_capacity, "Unit" : "MWh"},   
                "Areal energy capacity": {"Value": areal_energy_capacity, "Unit" : "kWh/m2"},
            },
            "Battery Cell Stack":{                             
                "Area": {"Value": cell_stack_area, "Unit" : "m2"},
                "Current density" : {"Value": current_density, "Unit" : "A/m2"},
                "Discharge voltage" : {"Value": discharge_voltage, "Unit" : "V"},
                "Lifetime": {"Value": lifetime, "Unit" : "year"},
            },  
            "Battery Electrolyte":{
                "Energy density": {"Value": Energy_density, "Unit" : "Wh/kg"},
                "Fraction of electrolyte to replace per year": {"Value": electrolyte_replacement, "Unit" : "-"},    
                "Fraction of recyclable electrolyte": {"Value": electrolyte_regeneration, "Unit" : "-"},                
                "Electrolyte density": {"Value": electrolyte_density, "Unit" : "kg/m3"}
            },
            "Battery Periphery":{
                "Pumps lifetime": {"Value": pump_lifetime, "Unit" : "year"},
            },
            "RFB Specific Impacts": {
                "Electrolyte": {"GWP_Value": electrolyte_gwp, "GWP_Unit": "kg/kg",
                          "Energy_Value": electrolyte_energy, "Energy_Unit": "J/kg", 
                          "Toxicity_Value": electrolyte_toxicity, "Toxicity_Unit": "1/kg", 
                          "Resource_use_Value": electrolyte_resource_use, "Resource_use_Unit": "kg/kg" },  
            },                       
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_ones": {'Operation years ones': np.array([1,1, 1, 1])},       
                "Battery_power": 5,
                "Storage_capacity": 200,
                "areal_energy_capacity": 32, 
                "cell_stack_area": 6,
                "current_density": 200, 
                "discharge_voltage": 1.25,
                "lifetime": 2,
                "Energy_density": 40,
                "electrolyte_replacement": 0.05,
                "electrolyte_regeneration": 0.6,
                "pump_lifetime": 2,
                "electrolyte_density": 1400,
                "electrolyte_gwp":20,
                "electrolyte_energy":100,
                "electrolyte_toxicity":12,
                "electrolyte_resource_use":15,                                                       
            },
            "expected": {
                "number_cell_stacks":Quantity(3334, '-'),
                "total_stack": Quantity(6668, '-'),
                "initial_electrolyte_amount": Quantity(5000, 'ton'),         
                "total_electrolyte": Quantity(5400, 'ton'),             
                "total_tank": Quantity(2517742.7575719818, 'kg'),                                                
                "total_electrolyte_gwp": Quantity(108000, 'ton'),                    
                "total_electrolyte_energy": Quantity(5.4e8, 'J'),                    
                "total_electrolyte_toxicity": Quantity(648e5, '-'),                    
                "total_electrolyte_resource_use": Quantity(81e3, 'ton'),
                "number_pumps": Quantity(6668, '-'), 
                "total_pumps": Quantity(13336, '-'), 
                "total_periphery": Quantity(1000, '-'), 
                "total_battery_gwp": Quantity(108000, 'ton'),                    
                "total_battery_energy": Quantity(5.4e8, 'J'),                    
                "total_battery_toxicity": Quantity(648e5, '-'),                    
                "total_battery_resource_use": Quantity(81e3, 'ton'),   
                "total_battery_land_use": Quantity(6250, 'm2'),                       
            },
        },
    ],
)
def test_RFB_plugin(case):
    """Test RFB_Plugin."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = RFB_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.number_cell_stacks.unit["-"] == pytest.approx(
        expected["number_cell_stacks"].unit["-"],
        abs=tolerance
    )

    assert plugin.total_stack.unit["-"] == pytest.approx(
        expected["total_stack"].unit["-"],
        abs=tolerance
    )

    assert plugin.initial_electrolyte_amount.unit["kg"] == pytest.approx(
        expected["initial_electrolyte_amount"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_electrolyte.unit["kg"] == pytest.approx(
        expected["total_electrolyte"].unit["kg"],
        abs=tolerance
    )    

    assert plugin.total_tank.unit["kg"] == pytest.approx(
        expected["total_tank"].unit["kg"],
        abs=tolerance
    )   

    assert plugin.number_pumps.unit["-"] == pytest.approx(
        expected["number_pumps"].unit["-"],
        abs=tolerance
    )   

    assert plugin.total_pumps.unit["-"] == pytest.approx(
        expected["total_pumps"].unit["-"],
        abs=tolerance
    ) 

    assert plugin.total_periphery.unit["-"] == pytest.approx(
        expected["total_periphery"].unit["-"],
        abs=tolerance
    )           


    assert plugin.total_electrolyte_gwp.unit["kg"] == pytest.approx(
        expected["total_electrolyte_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_electrolyte_energy.unit["J"] == pytest.approx(
        expected["total_electrolyte_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.total_electrolyte_toxicity.unit["-"] == pytest.approx(
        expected["total_electrolyte_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_electrolyte_resource_use.unit["kg"] == pytest.approx(
        expected["total_electrolyte_resource_use"].unit["kg"],
        abs=tolerance
    )   

    assert plugin.total_battery_gwp.unit["kg"] == pytest.approx(
        expected["total_battery_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_battery_energy.unit["MWh"] == pytest.approx(
        expected["total_battery_energy"].unit["MWh"],
        abs=tolerance
    )

    assert plugin.total_battery_toxicity.unit["-"] == pytest.approx(
        expected["total_battery_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_battery_resource_use.unit["ton"] == pytest.approx(
        expected["total_battery_resource_use"].unit["ton"],
        abs=tolerance
    )  

    assert plugin.total_battery_land_use.unit["m2"] == pytest.approx(
        expected["total_battery_land_use"].unit["m2"],
        abs=tolerance
    )               
