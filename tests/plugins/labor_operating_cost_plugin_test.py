import pytest
from pyH2A.Plugins.Labor_Operating_Cost_Plugin import Labor_Operating_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF object for Labor_Operating_Cost_Plugin with configurable inputs."""

    def __init__(
        self,
        staff,
        hourly_labor_cost,
        labor_inflator,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Inflation": {
                "Labor inflator": {
                    "Value": labor_inflator,
                    "Unit": "-"
                },
            },               
            "Fixed Operating Costs": {
                "Staff": {
                    "Value": staff,
                    "Unit": "-",
                },
                "Hourly labor cost": {
                    "Value": hourly_labor_cost,
                    "Unit": "USD / h",
                },
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "staff": 1.0,
                "hourly_labor_cost": 50.0,
                "labor_inflator": 1.05,
            },
            "expected": {
                "labor_uninflated": Quantity(104000.0, "USD"),
                "labor_inflated": Quantity(109200.0, "USD"),
            },
        },
    ],
)
def test_fixed_operating_cost_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Labor_Operating_Cost_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.labor_uninflated.unit['USD'] == pytest.approx(
        expected["labor_uninflated"].unit['USD'],
        abs=tolerance
    )

    assert plugin.labor_inflated.unit['USD'] == pytest.approx(
        expected["labor_inflated"].unit['USD'],
        abs=tolerance
    )

