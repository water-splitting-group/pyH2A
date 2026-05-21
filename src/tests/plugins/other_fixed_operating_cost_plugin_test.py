import pytest
from pyH2A.Plugins.Other_Fixed_Operating_Cost_Plugin import Other_Fixed_Operating_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF object for Fixed_Operating_Cost_Plugin with configurable inputs."""

    def __init__(
        self,
        other_fixed_costs,
        labor_cost,
        combined_inflator,
    ):
        self.inp = {
            "Fixed Operating Costs": {
                "Labor cost": {
                    "Value": labor_cost,
                    "Unit": "USD",
                },
            },

            "<...> Other Fixed Operating Cost <...>": {
                key: {
                    "Value": value,
                    "Unit": "USD"
                } 
            for key, value in other_fixed_costs.items()
            },
        }

        self.combined_inflator = combined_inflator


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "labor_cost": 109200.,
                "other_fixed_costs": {
                    "electrolyzer_OPEX": 0.2, 
                    "PV_OPEX": 0.2
                },
                "combined_inflator": 1.1,
            },
            "expected": {
                "total_fixed_operating_cost": Quantity(109200.44, "USD"),
            },
        },
    ],
)
def test_fixed_operating_cost_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Other_Fixed_Operating_Cost_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12


    assert plugin.total_fixed_operating_cost.unit['USD'] == pytest.approx(
        expected["total_fixed_operating_cost"].unit['USD'],
        abs=tolerance
    )
