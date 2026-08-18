import pytest
from pyH2A.Plugins.Inflation_Plugin import Inflation_Plugin
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """DCF object for Inflation_plugin with configurable inputs."""

    def __init__(
        self,
        inflation,
        current_year_capital_costs,
        basis_year,
        ref_year,
        time_dict,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Financial Input Values": {
                "Inflation rate": {
                    "Value": inflation, 
                    "Unit": "-", 
                },
                "Current year for capital costs": {
                    "Value": current_year_capital_costs, 
                    "Unit": "-", 
                },
                "Basis year": {
                    "Value": basis_year, 
                    "Unit": "-", 
                },      
                "Reference year": {
                    "Value": ref_year, 
                    "Unit": "-", 
                },             
            },
            "Time": {
                "Years": {
                    "Value": time_dict, 
                    "Unit": "-", 
                    "Processed": "Yes",                      
                },
            },
        }

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "inflation": 0.05,
                "current_year_capital_costs": 1000,
                "basis_year": 2025,
                "ref_year": 2020,
                "time_dict": {
                    "Plant years relative": np.arange(0,2), 
                    "Startup time offset": 5,
                }
            },
           "expected": {
                "inflation_factor_full": Quantity(np.array([1, 1.05]), "-"),
                "inflation_correction": Quantity(1.27628156250, "-"),
                "cepci_inflator": Quantity(0.6612516152852131, "-"),
                "ci_inflator": Quantity(1.5993140978402587, "-"),   
                "combined_inflator": Quantity(1.0575490305452844, "-"), 
                "labor_inflator": Quantity(1.0, "-"), 
                "chemical_inflator": Quantity(1.0, "-"),                                                                   
            },
        }
    ],
    ids=[
        "Realistic case - Time Plugin",
    ]
)
def test_inflation_plugin(case):
    """Check plugin returns correct time-related quantities."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Inflation_Plugin(dcf, print_info=False)
    expected = case["expected"]

    atol = 1e-12

    np.testing.assert_allclose(
        plugin.inflation_factor_full.unit["-"],
        expected["inflation_factor_full"].unit["-"],
        rtol=1e-12,  
        atol=1e-12,  
    )   

    assert plugin.inflation_correction.unit["-"] == pytest.approx(
        expected["inflation_correction"].unit["-"],
        abs=atol
    )

    assert plugin.cepci_inflator.unit["-"] == pytest.approx(
        expected["cepci_inflator"].unit["-"],
        abs=atol
    )

    assert plugin.ci_inflator.unit["-"] == pytest.approx(
        expected["ci_inflator"].unit["-"],
        abs=atol
    )

    assert plugin.combined_inflator.unit["-"] == pytest.approx(
        expected["combined_inflator"].unit["-"],
        abs=atol
    )

    assert plugin.labor_inflator.unit["-"] == pytest.approx(
        expected["labor_inflator"].unit["-"],
        abs=atol
    )

    assert plugin.chemical_inflator.unit["-"] == pytest.approx(
        expected["chemical_inflator"].unit["-"],
        abs=atol
    )

