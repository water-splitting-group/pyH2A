import pytest
import numpy as np
from pyH2A.Plugins.Variable_Operating_Cost_Plugin import Variable_Operating_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF for Variable_Operating_Cost_Plugin with variable-value inputs."""

    def __init__(
        self, 
        plant_output_per_year, 
        utilities, 
        other_variable_costs, 
        inflation_correction,
        chemical_inflator
    ):  
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Output per year": {"Value": plant_output_per_year, "Unit":"kg"}
            },
            "Utilities": {
                key: {
                    "Cost_Value": value["Cost"], "Cost_Unit":"USD",
                    "Usage_Value": value["Usage"], "Usage_Unit":"-/kg", "Usage_Path": "",
                    "Price_Conversion_Factor_Value": value.get("Conversion", 1.0), "Price_Conversion_Factor_Unit": "-",
                } 
                for key, value in utilities.items()
            },
            "Dummy Left Other Variable Operating Cost Dummy Right": {
                key: {
                    "Value": value["Cost_Value"],
                    "Unit": "USD"
                }
                for key, value in other_variable_costs.items()
            }
        }
        
        self.inflation_correction = inflation_correction
        self.chemical_inflator = chemical_inflator
        self.inflation_factor = np.ones(10)  
        self.years = np.arange(2026, 2036) 
          

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_output_per_year": 100_000.0,  
                "utilities": {
                    "Electricity": {"Cost": 0.05, "Usage": 50.0, "Conversion": 2.0}, 
                    "Water": {"Cost": 0.01, "Usage": 10.0}          
                },
                "other_variable_costs": {
                    "Maintenance": {
                        "Cost_Value": 1000.0,
                        "Cost_Unit": "USD"
                    },
                    "Chemicals": {
                        "Cost_Value": 500.0,
                        "Cost_Unit": "USD"
                    }
                },
                "inflation_correction": 1.2,
                "chemical_inflator": 1.0
            },
            "expected": {
                "utilities": Quantity(np.array([612000.0, 612000.0, 612000.0, 612000.0, 612000.0, 612000.0, 612000.0,
              612000.0, 612000.0, 612000.0]), "USD"),
                "other": Quantity(np.array(1500.), "USD")                                      
            }
        }
    ]
)
def test_variable_operating_cost_plugin(case):
    """Test Variable_Operating_Cost_Plugin using variable-value inputs."""

    # Create DummyDCF
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Variable_Operating_Cost_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.utilities.unit["USD"], 
        expected["utilities"].unit["USD"], 
        rtol=tolerance
    )
    
    np.testing.assert_allclose(
        plugin.other.unit["USD"], 
        expected["other"].unit["USD"], 
        rtol=tolerance
    )
