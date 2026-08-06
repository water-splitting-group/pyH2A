import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Battery_Calculation_Plugin import Battery_Calculation_Plugin
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Battery_Calculation_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        available_energy_hourly, 
        unsatisfied_demand, 
        design_capacity,
        lowest_discharge_level,
        capacity_loss,
        highest_charge_level,
        rte, 
        power,
        charging_threshold,
        capacity_per_module
    ):
                
        self.functional_unit = resolve_functional_unit('kWh')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },            
            "Power Generation": {
                "Available energy (hourly)": {"Value": available_energy_hourly, "Unit" : "kWh"},
            },         
            "Hourly Consumer Profile": {"Unsatisfied demand": {"Value": unsatisfied_demand, "Unit" : "kWh"}},      
            "Battery": {
                "Design capacity": {
                    "Value": design_capacity,
                    "Unit": "MWh",   
                },
                "Lowest discharge level": {
                    "Value": lowest_discharge_level,
                    "Unit": "-",   
                }, 
                "Capacity loss per year": {
                    "Value": capacity_loss,
                    "Unit": "-",   
                },        
                "Highest charge level": {
                    "Value": highest_charge_level,
                    "Unit": "-",   
                },      
                "Round trip efficiency": {
                    "Value": rte,
                    "Unit": "-",   
                },  
                "Power": {
                    "Value": power,
                    "Unit": "MW",   
                },  
                "Charging threshold": {
                    "Value": charging_threshold,
                    "Unit": "-",   
                }, 
                "Storage capacity per battery module": {
                    "Value": capacity_per_module,
                    "Unit": "MWh",   
                },                                                                                                                          
            },             
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {'Operation years relative': np.arange(0, 2)},       
                "available_energy_hourly": {0: 2*np.arange(0, 8760), 1:2*np.arange(0, 8760)},
                "unsatisfied_demand": {0: 3*np.arange(0, 8760), 1:np.arange(0, 8760)},
                "design_capacity": 30,
                "lowest_discharge_level": 0.2,
                "capacity_loss": 0.1, 
                "highest_charge_level": 0.8, 
                "rte":0.8, 
                "power":10,
                "charging_threshold":0.2, 
                "capacity_per_module": 5

            },
            "expected": {
                "first_6h_houly_state_of_energy":Quantity(np.array([
                    24, 23.997 , 23.991 , 
                     23.982, 23.97 ,  23.955
                    ]), 'MWh'),
                "first_6h_hourly_unstored_energy":Quantity(np.array([
                    0, 0.002, 0.004, 
                    0.006, 0.008, 0.01
                    ]), 'MWh'),                    
                "total_unstored_energy":Quantity(53977.26, 'MWh'),
                "last_6h_hourly_unsatisfied_demand":Quantity(np.array([
                    16.262 , 16.265 , 16.268, 
                    16.271, 16.274, 16.277
                    ]), 'MWh'),                        
                "total_unsatisfied_demand":Quantity(53978.76, 'MWh'),
                "number_charge_cycles":Quantity(0.56, '-'),   
                "number_modules": Quantity(6, '-')                
            },
        },
    ],
)
def test_battery_calculation_plugin(case):
    """Test Battery_Calculation_Plugin."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Battery_Calculation_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.houly_state_of_energy[0].unit["J"][0:6] == pytest.approx(
        expected["first_6h_houly_state_of_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.hourly_unstored_energy[0].unit["J"][0:6] == pytest.approx(
        expected["first_6h_hourly_unstored_energy"].unit["J"],
        abs=tolerance
    )    

    assert plugin.total_unstored_energy.unit["J"] == pytest.approx(
        expected["total_unstored_energy"].unit["J"],
        abs=tolerance
    )    

    assert plugin.hourly_unsatisfied_demand[0].unit["J"][-6:] == pytest.approx(
        expected["last_6h_hourly_unsatisfied_demand"].unit["J"],
        abs=tolerance
    )    

    assert plugin.total_unsatisfied_demand.unit["J"] == pytest.approx(
        expected["total_unsatisfied_demand"].unit["J"],
        abs=tolerance
    )    

    assert plugin.number_charge_cycles.unit["-"] == pytest.approx(
        expected["number_charge_cycles"].unit["-"],
        abs=tolerance
    )       

    assert plugin.number_modules.unit["-"] == pytest.approx(
        expected["number_modules"].unit["-"],
        abs=tolerance
    )       