import pytest
import numpy as np
from pyH2A.Plugins.Replacement_Plugin import Replacement_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class DummyDCF:
    """Minimal DCF object for Replacement_Plugin with simple variable-value inputs."""
    def __init__(
        self,
        plant_years_relative, 
        combined_inflator,
        inflation_correction,
        inflation_factor,               
        planned_replacement,
        unplanned_replacement,
    ):
        self.inp = {
            "Time": {
                "Years": {
                    "Value": plant_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },    
            "Inflation": {
                "Combined inflator": {
                    "Value": combined_inflator,
                    "Unit": "-"
                },
                "Inflation correction": {
                    "Value": inflation_correction,
                    "Unit": "-"
                },
                "Inflation factor full": {
                    "Value": inflation_factor,
                    "Unit": "-",
                    "Processed": "Yes",                                        
                },                
            },                              
            "Planned Replacement": {
                key: {"Cost_Value": value["cost"],
                      "Cost_Unit": "USD", 
                      "Frequency_Value": value["frequency"],
                      "Frequency_Unit": "year"}
                for key, value in planned_replacement.items()
            },
            "Dummy Left Unplanned Replacement Dummy Right": {
                key: {"Value": value, 
                      "Unit":"USD"} 
                for key, value in unplanned_replacement.items()
            }
        }
        

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_years_relative":{"Plant years relative":np.arange(1, 11)},
                "combined_inflator": 1.0,
                "inflation_correction": 1.0,
                "inflation_factor": np.ones(10),
                "planned_replacement": {
                    "Electrolyzer Stack": {
                        "cost": 5000.,
                        "frequency": 5.
                    },
                    "Valve": {
                        "cost": 2000.,
                        "frequency": 3.
                    },
                },
                "unplanned_replacement": {
                    "Misc": 1000.
                },
            },
            "expected": {
                "total": Quantity(26000.0, "USD"),
            },
        }
    ]
)
def test_replacement_plugin(case):
    """Test Replacement_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Replacement_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12
    
    assert np.sum(plugin.yearly) == pytest.approx(
        expected["total"].unit["USD"],
        abs=tolerance
    )
