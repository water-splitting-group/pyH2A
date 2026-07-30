import pytest
import numpy as np
from pyH2A.Plugins.Finance.Variable_Operating_Cost_Plugin import Variable_Operating_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF for Variable_Operating_Cost_Plugin with variable-value inputs."""

    def __init__(
        self,
        time_values,
        inflation_correction,
        chemical_inflator,
        inflation_factor_full,
        start_up_time,
        fraction_during_start_up,
        plant_output_per_year,
        capacity_factor,
        utilities,
        other_variable_costs
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": time_values,
                    "Unit": "-",
                    "Processed": "Yes",
                },
            },
            "Inflation": {
                "Inflation correction": {
                    "Value": inflation_correction,
                    "Unit": "-"
                },
                "Chemical inflator": {
                    "Value": chemical_inflator,
                    "Unit": "-"
                },
                "Inflation factor full": {
                    "Value": inflation_factor_full,
                    "Unit": "-",
                    "Processed": "Yes",
                },
            },
            "Financial Input Values": {
                "Start-up time": {
                    "Value": start_up_time,
                    "Unit": "year"
                },
                "Fraction of variable operating costs during start-up": {
                    "Value": fraction_during_start_up,
                    "Unit": "-"
                },
            },
            "Technical Operating Parameters and Specifications": {
                "Design output by year": {
                    "Value": plant_output_per_year, 
                    "Unit": "kg",
                    "Processed": "Yes",
                    },
                "Operating capacity factor": {
                    "Value": capacity_factor,
                    "Unit": "-",
                },
            },
            "Utilities": {
                key: {
                    "Cost_Value": value["Cost"], 
                    "Cost_Unit": "USD", 
                    "Usage_Value": value["Usage"], 
                    "Usage_Unit": "1/kg", 
                    "Price_Conversion_Factor_Value": value.get("Conversion", 1.0),
                    "Price_Conversion_Factor_Unit": "-",
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
          

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "time_values":{
                    "Operation years":np.arange(2026, 2036),
                    "Operation years ones": np.ones(10),
                    "Analysis years ones": np.ones(12),
                    "Start index": 2,
                },
                "inflation_correction": 1.2,
                "chemical_inflator": 1.0,
                "inflation_factor_full": np.array([1.00, 1.01, 1.02, 1.03, 1.04, 1.05,
                                                    1.06, 1.07, 1.08, 1.09, 1.10, 1.11]),
                "start_up_time": 1,
                "fraction_during_start_up": 0.6,
                "plant_output_per_year": np.array([125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0,
                                                   125_000.0]),  
                "capacity_factor": 0.8,
                "utilities": {
                    "Electricity": {
                        "Cost": 0.05, 
                        "Usage": 50.0, 
                        "Conversion": 2.0}, 
                    "Water": {
                        "Cost": 0.01, 
                        "Usage": 10.0}          
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
            },
            "expected": {
                "utilities": Quantity(np.array([612000.0, 
                                                612000.0, 
                                                612000.0, 
                                                612000.0, 
                                                612000.0, 
                                                612000.0, 
                                                612000.0,
                                                612000.0, 
                                                612000.0, 
                                                612000.0]), 
                                        "USD"),
                "other": Quantity(np.array(1500.), "USD"),
                "annual_variable_operating_cost": Quantity(
                    np.array([0., 0., 375462., 631905., 638040., 644175., 650310.,
                              656445., 662580., 668715., 674850., 680985.]),
                    "USD"),
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

    np.testing.assert_allclose(
        plugin.annual_variable_operating_cost.unit["USD"],
        expected["annual_variable_operating_cost"].unit["USD"],
        atol=tolerance
    )
