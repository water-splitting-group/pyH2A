import pytest
from pyH2A.Plugins.Core.Time_Plugin import Time_Plugin
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from tests.Utilities.check_dicts_for_testing import check_dicts
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """DCF object for Time_plugin with configurable inputs."""

    def __init__(
        self,
        construction, 
        plant_life,
        startup_year,
        ref_year,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Construction":{
                key:{
                    "Value": value, 
                    "Unit": "-"
                }
                for key, value in construction.items()          
            },
            "Financial Input Values": {
                "Plant life": {
                    "Value": plant_life, 
                    "Unit": "year", 
                },
                "Assumed start-up year": {
                    "Value": startup_year, 
                    "Unit": "-", 
                },      
                "Reference year": {
                    "Value": ref_year, 
                    "Unit": "-", 
                },             
            },
        }

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "construction": {
                    "year 0": 0.5,
                    "year 1": 0.5},
                "plant_life": 5,
                "startup_year": 2030,
                "ref_year": 2020,
            },
           "expected": {
                "Startup time offset": Quantity(10, "-"),
                "Plant years relative": Quantity(np.arange(-2,5), "-"),
                "Operation years": Quantity(np.arange(2030,2035), "-"),
                "Operation years relative": Quantity(np.arange(0,5), "-"),   
                "Start index": Quantity(2, "-"),
                "Operation years ones": Quantity(np.ones(5), "-"),    
                "Analysis years ones": Quantity(np.ones(7), "-"),   
                "Construction years ones": Quantity(np.ones(2), "-"),   
            },
        }
    ],
    ids=[
        "Realistic case - Time Plugin",
    ]
)

def test_time_plugin(case):
    """Check plugin returns correct time-related quantities."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Time_Plugin(dcf, print_info=False)
    expected = case["expected"]

    check_dicts(plugin.time_quantities_dict, expected)