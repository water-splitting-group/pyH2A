import pytest
import numpy as np
from pyH2A.Plugins.Other_Fixed_Operating_Cost_Plugin import Other_Fixed_Operating_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF object for Fixed_Operating_Cost_Plugin with configurable inputs."""

    def __init__(
        self,
        other_fixed_costs,
        labor_cost,
        combined_inflator,
        analysis_years_ones,
        start_index,
        inflation_correction,
        inflation_factor_full,
        start_up_time,
        fraction_during_start_up,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {
                        "Analysis years ones": analysis_years_ones,
                        "Start index": start_index,
                    },
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
                "Fraction of fixed operating costs during start-up": {
                    "Value": fraction_during_start_up,
                    "Unit": "-"
                },
            },
            "Fixed Operating Costs": {
                "Labor cost - inflated": {
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
                "analysis_years_ones": np.ones(5),
                "start_index": 2,
                "inflation_correction": 1.02,
                "inflation_factor_full": np.array([1.0, 1.05, 1.10, 1.15, 1.20]),
                "start_up_time": 1,
                "fraction_during_start_up": 0.5,
            },
            "expected": {
                "total_fixed_operating_cost": Quantity(109200.44, "USD"),
                "annual_fixed_operating_cost": np.array(
                    [0.0, 0.0, 61261.44684, 128092.11612, 133661.33856]
                ),
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

    np.testing.assert_allclose(
        plugin.annual_fixed_operating_cost.unit['USD'],
        expected["annual_fixed_operating_cost"],
        atol=tolerance
    )
