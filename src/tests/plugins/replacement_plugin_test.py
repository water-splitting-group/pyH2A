import pytest
import numpy as np
from pyH2A.Plugins.Finance.Replacement_Plugin import Replacement_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from tests.Utilities.check_dicts_for_testing import check_dicts
from pyH2A.Utilities.functional_unit import resolve_functional_unit

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
        self.functional_unit = resolve_functional_unit('kg')
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
                "plant_years_relative":{
                    "Plant years relative": np.arange(1, 11), 
                    "Start index": 2},
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
                "yearly": Quantity(np.array([0.,
                                             0., 
                                              3000., 
                                              1000., 
                                              6000., 
                                              3000., 
                                              1000., 
                                              1000., 
                                              3000., 
                                              6000.]), "USD"),
                "contributions": {
                    'Data': {
                        'Electrolyzer Stack': Quantity(10000.0, 'USD'),
                        'Unplanned Replacement': Quantity(10000.0, 'USD'),
                        'Valve': Quantity(6000.0, 'USD')
                    },
                    'Table Group': 'Replacement Costs',
                    'Total': Quantity(26000.0, 'USD')
                }
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

    np.testing.assert_allclose(
        plugin.yearly_inflated.unit['USD'],
        expected["yearly"].unit['USD'],
        atol=tolerance
    )

    check_dicts(plugin.contributions, expected["contributions"], tolerance)
