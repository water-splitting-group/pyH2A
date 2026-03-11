import pytest
import numpy as np
from pyH2A.Plugins.Fixed_Operating_Cost_Plugin import Fixed_Operating_Cost_Plugin


class DummyDCF:
    """Minimal DCF object for Fixed_Operating_Cost_Plugin with configurable inputs."""

    def __init__(
        self,
        staff,
        hourly_labor_cost,
        other_fixed_costs,
        labor_inflator,
        combined_inflator,
    ):
        self.inp = {
            "Fixed Operating Costs": {
                "staff": {"Value": staff},
                "hourly labor cost": {"Value": hourly_labor_cost},
            },
            "Dummy Left Other Fixed Operating Cost Dummy Right": {
                key: {"Value": value} for key, value in other_fixed_costs.items()
            },
        }

        self.labor_inflator = labor_inflator
        self.combined_inflator = combined_inflator


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "staff": 1,
                "hourly_labor_cost": 50.0,
                "other_fixed_costs": {
                    "electrolyzer_OPEX": 0.2, 
                    "PV_OPEX": 0.2
                },
                "labor_inflator": 1.05,
                "combined_inflator": 1.1,
            },
            "expected": {
                "labor_uninflated": 104000.0,
                "labor": 109200.0,
                "other": 0.44000000000000006,
            },
        },
    ],
)
def test_fixed_operating_cost_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Fixed_Operating_Cost_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.labor_uninflated == pytest.approx(
        expected["labor_uninflated"],
        abs=tolerance
    )
    
    assert plugin.labor == pytest.approx(
        expected["labor"],
        abs=tolerance
    )
    
    assert plugin.other == pytest.approx(
        expected["other"],
        abs=tolerance
    )
