import pytest
from pyH2A.Plugins.Time_Plugin import Time_Plugin
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class DummyDCF:
    """DCF object for Time_plugin with configurable inputs."""

    def __init__(
        self,
        construction, 
        plant_life,
        startup_year,
        ref_year,
    ):
        self.inp = {
            "Construction":{
                key:{
                    "Value": value, 
                    "Unit": "-"
                }
                for key, value in construction.items()          
            },
            "Financial Input Values": {
                "plant life": {
                    "Value": plant_life, 
                    "Unit": "year", 
                },
                "startup year": {
                    "Value": startup_year, 
                    "Unit": "-", 
                },      
                "ref year": {
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
                "construction": {"year 0":0.5, "year 1":0.5},
                "plant_life": 5,
                "startup_year": 2030,
                "ref_year": 2020,
            },
           "expected": {
                "startup_time_offset": Quantity(10, "-"),
                "plant_years_relative": Quantity(np.arange(-2,5), "-"),
                "operation_years": Quantity(np.arange(2030,2035), "-"),
                "operation_years_relative": Quantity(np.arange(0,5), "-"),   
                "operation_years_ones": Quantity(np.ones(5), "-"),                                   
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


    assert plugin.startup_time_offset.unit["-"] == pytest.approx(
        expected["startup_time_offset"].unit["-"],
        abs=1e-12
    )

    np.testing.assert_allclose(
        plugin.plant_years_relative.unit["-"],
        expected["plant_years_relative"].unit["-"],
        rtol=1e-12,  
        atol=1e-12,  
    )

    np.testing.assert_allclose(
        plugin.operation_years.unit["-"],
        expected["operation_years"].unit["-"],
        rtol=1e-12,  
        atol=1e-12,  
    )

    np.testing.assert_allclose(
        plugin.operation_years_relative.unit["-"],
        expected["operation_years_relative"].unit["-"],
        rtol=1e-12,  
        atol=1e-12,  
    )    

    np.testing.assert_allclose(
        plugin.operation_years_ones.unit["-"],
        expected["operation_years_ones"].unit["-"],
        rtol=1e-12,  
        atol=1e-12,  
    )   