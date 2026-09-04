import pytest
import numpy as np
from pyH2A.Plugins.Production_Plugin import Production_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """Minimal DCF object for Production_Plugin testing with configurable inputs."""
    
    def __init__(
        self,
        operation_years_ones,
        plant_design_capacity,
        operating_capacity_factor,
        design_output_by_year,
        fraction_of_output_that_reaches_gate,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        if design_output_by_year is None:
            self.inp = {
                "Time": {
                    "Years": {
                        "Value": operation_years_ones,
                        "Unit": "-",   
                        "Processed": "Yes",                    
                    },
                },                   
                "Technical Operating Parameters and Specifications": {
                    "Plant design capacity": {
                        "Value": plant_design_capacity, 
                        "Unit":"kg/year"
                    },
                    "Operating capacity factor": {
                        "Value": operating_capacity_factor, 
                        "Unit":"-"
                    },
                    "Fraction of output that reaches gate": {
                        "Value": fraction_of_output_that_reaches_gate, 
                        "Unit":"-"
                    },
                },        
            }

        else:
            self.inp = {
                "Time": {
                    "Years": {
                        "Value": operation_years_ones,
                        "Unit": "-",   
                        "Processed": "Yes",                    
                    },
                },                  
                "Technical Operating Parameters and Specifications": {
                    "Operating capacity factor": {
                        "Value": operating_capacity_factor, 
                        "Unit": "-"
                    },
                    "Design output by year": {
                        "Value": design_output_by_year, 
                        "Unit": "kg",
                        "Processed": "Yes",
                    },
                    "Fraction of output that reaches gate": {
                        "Value": fraction_of_output_that_reaches_gate,
                        "Unit": "-"
                    },
                },           
            }    


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_ones": {"Operation years ones": np.ones(4)},                
                "plant_design_capacity": 1000.0,
                "operating_capacity_factor": 0.9,
                "design_output_by_year": None,
                "fraction_of_output_that_reaches_gate": 0.8,
            },
            "expected": {
                "design_output_by_year": Quantity(
                                                np.array(
                                                        [1000., 1000., 1000., 1000. ]
                                                ),
                                                "kg"
                                        ),
                "sum_design_output": Quantity(4000.0,"kg"),
                "output_per_year_at_gate": Quantity(
                                                np.array(
                                                        [720., 720., 720., 720. ]
                                                ),
                                                "kg"
                                        ),
                "sum_output_gate": Quantity(2880.0,"kg")
            }
        }, 
        {
            "input": {
                "operation_years_ones": {"Operation years ones": np.ones(4)},
                "plant_design_capacity": None,
                "operating_capacity_factor": 0.9,
                "design_output_by_year": np.array([1000., 1000., 1000., 1000. ]),
                "fraction_of_output_that_reaches_gate": 0.8,
            },
            "expected": {
                "design_output_by_year": Quantity(
                                                np.array(
                                                        [1000., 1000., 1000., 1000. ]
                                                ),
                                                "kg"
                                        ),
                "sum_design_output": Quantity(4000.0,"kg"),
                "output_per_year_at_gate": Quantity(
                                                np.array(
                                                        [720., 720., 720., 720. ]
                                                ),
                                                "kg"
                                        ),
                "sum_output_gate": Quantity(2880.0,"kg")
            }
        },         
    ]
)
def test_production_plugin(case):
    """Test Production_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Production_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12
    
    assert plugin.sum_design_output.unit["kg"] == pytest.approx(
        expected["sum_design_output"].unit["kg"],
        abs=tolerance
    )

    assert plugin.sum_output_gate.unit["kg"] == pytest.approx(
        expected["sum_output_gate"].unit["kg"],
        abs=tolerance
    )    

    np.testing.assert_allclose(
        plugin.design_output_by_year.unit['kg'],
        expected["design_output_by_year"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )    

    np.testing.assert_allclose(
        plugin.sum_output_gate.unit['kg'],
        expected["sum_output_gate"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )     