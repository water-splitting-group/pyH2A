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
        Power_per_cell_stack, 
        Cost_per_cell_stack,
        Storage_capacity, 
        Energy_density, 
        electrolyte_regeneration, 
        Specific_GWP,
        Energy_intensity, 
        Specific_toxicity, 
        Specific_resource_use, 
        Specific_cost
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
                "Power per cell stack": {"Value": Power_per_cell_stack, "Unit" : "kW"},
                "Cost per cell stack": {"Value": Cost_per_cell_stack, "Unit" : "USD"},
                "Design capacity": {"Value": Storage_capacity, "Unit" : "MWh"},
                "Energy density": {"Value": Energy_density, "Unit" : "Wh/kg"},
                "Electrolyte regeneration per year": {"Value": electrolyte_regeneration, "Unit" : "-"},
            },  
            "Electrolyte Impact": {
                "Specific GWP": {"Value": Specific_GWP, "Unit" : "kg/kg"},
                "Energy intensity": {"Value": Energy_intensity, "Unit" : "kWh/kg"},
                "Specific toxicity": {"Value": Specific_toxicity, "Unit" : "1/kg"},
                "Specific resource use": {"Value": Specific_resource_use, "Unit" : "kg/kg"},
                "Specific cost": {"Value": Specific_cost, "Unit" : "USD/kg"},
            },                       
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_ones": {'Operation years ones': np.array([1,1])},       
                "Battery_power": 5,
                "Power_per_cell_stack": 10,
                "Cost_per_cell_stack": 10000,
                "Storage_capacity": 200,
                "Energy_density": 40,
                "electrolyte_regeneration": 0.01,
                "Specific_GWP":20,
                "Energy_intensity":100,
                "Specific_toxicity":12,
                "Specific_resource_use":15,
                "Specific_cost": 10
            },
            "expected": {
                "number_cell_stacks":Quantity(500, '-'),
                "cost_cell_stacks": Quantity(5e6, 'USD'),
                "initial_electrolyte_amount": Quantity(5000, 'ton'),                    
                "yearly_electrolyte_amount": Quantity(50, 'ton'),                    
                "total_electrolyte_amount": Quantity(5100, 'ton'),                    
                "total_gwp": Quantity(102000, 'ton'),                    
                "total_energy": Quantity(510, 'GWh'),                    
                "total_toxicity": Quantity(61200000, '-'),                    
                "total_resource_use": Quantity(76500, 'ton'),          
                "yearly_cost":Quantity(5e5, 'USD')                            
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

    assert plugin.cost_cell_stacks.unit["USD"] == pytest.approx(
        expected["cost_cell_stacks"].unit["USD"],
        abs=tolerance
    )

    assert plugin.initial_electrolyte_amount.unit["kg"] == pytest.approx(
        expected["initial_electrolyte_amount"].unit["kg"],
        abs=tolerance
    )

    assert plugin.yearly_electrolyte_amount.unit["kg"] == pytest.approx(
        expected["yearly_electrolyte_amount"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_electrolyte_amount.unit["kg"] == pytest.approx(
        expected["total_electrolyte_amount"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_gwp.unit["kg"] == pytest.approx(
        expected["total_gwp"].unit["kg"],
        abs=tolerance
    )

    assert plugin.total_energy.unit["J"] == pytest.approx(
        expected["total_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.total_toxicity.unit["-"] == pytest.approx(
        expected["total_toxicity"].unit["-"],
        abs=tolerance
    )                    

    assert plugin.total_resource_use.unit["kg"] == pytest.approx(
        expected["total_resource_use"].unit["kg"],
        abs=tolerance
    )    

    assert plugin.yearly_cost.unit["USD"] == pytest.approx(
        expected["yearly_cost"].unit["USD"],
        abs=tolerance
    )        