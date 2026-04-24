import pytest
import numpy as np
from pyH2A.Plugins.Variable_Operating_Cost_Plugin import Variable_Operating_Cost_Plugin


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
                "Output per Year": {"Value": plant_output_per_year}
            },
            "Utilities": {
                key: {
                    "Cost": value["Cost"],
                    "Usage per kg H2": value["Usage"],
                    "Price Conversion Factor": value.get("Conversion", 1.0)
                } for key, value in utilities.items()
            },
            "Dummy Left Other Variable Operating Cost Dummy Right": {
                key: {"Value": value} for key, value in other_variable_costs.items()
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
                    "Maintenance": 1000.0,
                    "Chemicals": 500.0
                },
                "inflation_correction": 1.2,
                "chemical_inflator": 1.0
            },
            "expected": {
                "utilities": np.array([612000.0, 612000.0, 612000.0, 612000.0, 612000.0, 612000.0, 612000.0,
              612000.0, 612000.0, 612000.0]), 
                "other": np.array(1500.),                                      
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
        plugin.utilities, 
        expected["utilities"], 
        rtol=tolerance
    )
    
    np.testing.assert_allclose(
        plugin.other, 
        expected["other"], 
        rtol=tolerance
    )
