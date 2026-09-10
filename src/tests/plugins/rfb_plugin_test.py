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
        Power_per_cell_stack, 
        lifetime,
        Energy_density, 
        electrolyte_replacement, 
        electrolyte_production,
        electrolyte_density,
        periphery,
        stack_gwp, 
        stack_energy, 
        stack_toxicity, 
        stack_resource_use,
        electrolyte_gwp, 
        electrolyte_energy, 
        electrolyte_toxicity, 
        electrolyte_resource_use,
        periphery_gwp, 
        periphery_energy, 
        periphery_toxicity, 
        periphery_resource_use,
        steel_gwp, 
        steel_energy, 
        steel_toxicity, 
        steel_resource_use,
    ):
        
        self.functional_unit = resolve_functional_unit('kWh')        
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
            },
            "Battery Cell Stack":{                             
                "Power per cell stack": {"Value": Power_per_cell_stack, "Unit" : "kW"},
                "Lifetime": {"Value": lifetime, "Unit" : "year"},
            },  
            "Battery Electrolyte":{
                "Energy density": {"Value": Energy_density, "Unit" : "Wh/kg"},
                "Fraction of electrolyte to replace per year": {"Value": electrolyte_replacement, "Unit" : "-"},    
                "Fraction of replaced electrolyte to produce per year": {"Value": electrolyte_production, "Unit" : "-"},                
                "Electrolyte density": {"Value": electrolyte_density, "Unit" : "kg/m3"}
            },
            "Battery Periphery":{
                "Number of periphery items": {"Value": periphery, "Unit" : "-"},
            },
            "RFB Specific Impacts": {
                "Stack": {"GWP_Value": stack_gwp, "GWP_Unit": "kg",
                          "Energy_Value": stack_energy, "Energy_Unit": "J", 
                          "Toxicity_Value": stack_toxicity, "Toxicity_Unit": "-", 
                          "Resource_use_Value": stack_resource_use, "Resource_use_Unit": "kg" },
                "Electrolyte": {"GWP_Value": electrolyte_gwp, "GWP_Unit": "kg/kg",
                          "Energy_Value": electrolyte_energy, "Energy_Unit": "J/kg", 
                          "Toxicity_Value": electrolyte_toxicity, "Toxicity_Unit": "1/kg", 
                          "Resource_use_Value": electrolyte_resource_use, "Resource_use_Unit": "kg/kg" },
                "Periphery": {"GWP_Value": periphery_gwp, "GWP_Unit": "kg",
                          "Energy_Value": periphery_energy, "Energy_Unit": "J", 
                          "Toxicity_Value": periphery_toxicity, "Toxicity_Unit": "-", 
                          "Resource_use_Value": periphery_resource_use, "Resource_use_Unit": "kg" },                          
                "Steel": {"GWP_Value": steel_gwp, "GWP_Unit": "kg/kg",
                          "Energy_Value": steel_energy, "Energy_Unit": "J/kg", 
                          "Toxicity_Value": steel_toxicity, "Toxicity_Unit": "1/kg", 
                          "Resource_use_Value": steel_resource_use, "Resource_use_Unit": "kg/kg" },     
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
                "Power_per_cell_stack": 10,
                "lifetime": 2,
                "Energy_density": 40,
                "electrolyte_replacement": 0.05,
                "electrolyte_production": 0.4,
                "periphery": 1,
                "electrolyte_density": 1400,
                "stack_gwp":20,
                "stack_energy":100,
                "stack_toxicity":12,
                "stack_resource_use":15,
                "electrolyte_gwp":20,
                "electrolyte_energy":100,
                "electrolyte_toxicity":12,
                "electrolyte_resource_use":15,    
                "periphery_gwp":20,
                "periphery_energy":100,
                "periphery_toxicity":12,
                "periphery_resource_use":15,
                "steel_gwp":20,
                "steel_energy":100,
                "steel_toxicity":12,
                "steel_resource_use":15,                                                          
            },
            "expected": {
                "number_cell_stacks":Quantity(500, '-'),
                "total_stack": Quantity(1000, '-'),
                "initial_electrolyte_amount": Quantity(5000, 'ton'),                    
                "total_electrolyte": Quantity(5400, 'ton'),                    
                "total_stack_gwp": Quantity(20, 'ton'),                    
                "total_stack_energy": Quantity(1e5, 'J'),                    
                "total_stack_toxicity": Quantity(12e3, '-'),                    
                "total_stack_resource_use": Quantity(15, 'ton'), 
                "total_electrolyte_gwp": Quantity(108000, 'ton'),                    
                "total_electrolyte_energy": Quantity(5.4e8, 'J'),                    
                "total_electrolyte_toxicity": Quantity(648e5, '-'),                    
                "total_electrolyte_resource_use": Quantity(81e3, 'ton'),  
                "total_periphery_gwp": Quantity(20, 'kg'),                    
                "total_periphery_energy": Quantity(100, 'J'),                    
                "total_periphery_toxicity": Quantity(12, '-'),                    
                "total_periphery_resource_use": Quantity(15, 'kg'),  
                "total_steel_gwp": Quantity(127585607.14285715, 'kg'),                    
                "total_steel_energy": Quantity(177.20223214285713888889, 'kWh'),                    
                "total_steel_toxicity": Quantity(76551364.28571428, '-'),                    
                "total_steel_resource_use": Quantity(95689.20535714287, 'ton'),        
                "total_battery_gwp": Quantity(235605.62714285713, 'ton'),                    
                "total_battery_energy": Quantity(327.230037698, 'kWh'),                    
                "total_battery_toxicity": Quantity(141363376.28571427, '-'),                    
                "total_battery_resource_use": Quantity(176704.22035714285, 'ton'),                                                                    
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

    assert plugin.total_stack_gwp.unit["kg"] == pytest.approx(
        expected["total_stack_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_stack_energy.unit["J"] == pytest.approx(
        expected["total_stack_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.total_stack_toxicity.unit["-"] == pytest.approx(
        expected["total_stack_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_stack_resource_use.unit["kg"] == pytest.approx(
        expected["total_stack_resource_use"].unit["kg"],
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

    assert plugin.total_periphery_gwp.unit["kg"] == pytest.approx(
        expected["total_periphery_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_periphery_energy.unit["J"] == pytest.approx(
        expected["total_periphery_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.total_periphery_toxicity.unit["-"] == pytest.approx(
        expected["total_periphery_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_periphery_resource_use.unit["kg"] == pytest.approx(
        expected["total_periphery_resource_use"].unit["kg"],
        abs=tolerance
    )   

    assert plugin.total_steel_gwp.unit["kg"] == pytest.approx(
        expected["total_steel_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_steel_energy.unit["MWh"] == pytest.approx(
        expected["total_steel_energy"].unit["MWh"],
        abs=tolerance
    )

    assert plugin.total_steel_toxicity.unit["-"] == pytest.approx(
        expected["total_steel_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_steel_resource_use.unit["kg"] == pytest.approx(
        expected["total_steel_resource_use"].unit["kg"],
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
