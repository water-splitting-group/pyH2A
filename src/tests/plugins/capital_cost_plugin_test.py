import pytest
import numpy as np
from pyH2A.Plugins.Capital_Cost_Plugin import Capital_Cost_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF object for Capital_Cost_Plugin with configurable inputs."""

    def __init__(
        self,
        direct_costs,
        indirect_costs,
        land_cost_per_acre,
        land_required_acres,
        other_non_depreciable_costs,
        combined_inflator,
        ci_inflator,
        analysis_years_ones,
        inflation_correction,
        inflation_factor_full,
        construction_fractions,
        fraction_equity_financing,
    ):

        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {"Analysis years ones": analysis_years_ones},
                    "Unit": "-",
                    "Processed": "Yes",
                },
            },
            "Inflation": {
                "Combined inflator": {
                    "Value": combined_inflator,
                    "Unit": "-"
                },
                "CI inflator": {
                    "Value": ci_inflator,
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
            "Construction": {
                key: {
                    "Value": value,
                    "Unit": "-"
                }
                for key, value in construction_fractions.items()
            },
            "Financial Input Values": {
                "Fraction equity financing": {
                    "Value": fraction_equity_financing,
                    "Unit": "-"
                },
            },
            "<...> Direct Capital Cost <...>": {
                key: {
                    "Value": value,
                    "Unit": "USD"
                }
                for key, value in direct_costs.items()
            },
            "<...> Indirect Capital Cost <...>": {
                key: {
                    "Value": value,
                    "Unit": "USD"
                }
                for key, value in indirect_costs.items()
            },
            "Non-Depreciable Capital Costs": {
                "Cost of land": {
                    "Value": land_cost_per_acre,
                    "Unit": "USD/acre"
                },
                "Land required": {
                    "Value": land_required_acres,
                    "Unit": "acre"
                },
            },
            "Dummy Left Other Non-Depreciable Capital Cost Dummy Right": {
                key: {
                    "Value": value,
                    "Unit": "USD"
                }
                for key, value in other_non_depreciable_costs.items()
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "direct_costs": {
                    "PV": 4500000.0,
                    "Electrolyzer": 4300000.0,
                    "Battery": 0.0,
                    "Reverse Osmosis": 600000.0,
                },
                "indirect_costs": {
                    "Engineering": 1200000.0,
                    "Contingency": 800000.0,
                },
                "land_cost_per_acre": 500.0,
                "land_required_acres": 2.0,
                "other_non_depreciable_costs": {
                    "Permits": 250000.0,
                },
                "combined_inflator": 1.10,
                "ci_inflator": 1.05,
                "analysis_years_ones": np.ones(5),
                "inflation_correction": 1.02,
                "inflation_factor_full": np.array([1.0, 1.05, 1.10, 1.15, 1.20]),
                "construction_fractions": {
                    "Year 1": 0.6,
                    "Year 2": 0.4,
                },
                "fraction_equity_financing": 0.6,
            },
            "expected": {
                "direct": Quantity(9400000.0, "USD"),
                "direct_inflated": Quantity(10340000.0, "USD"),
                "indirect": Quantity(2000000.0, "USD"),
                "indirect_inflated": Quantity(2200000.0, "USD"),
                "depreciable": Quantity(11400000.0, "USD"),
                "depreciable_inflated": Quantity(12540000.0, "USD"),
                "non_depreciable": Quantity(251000.0, "USD"),
                "non_depreciable_inflated": Quantity(263550.0, "USD"),
                "total": Quantity(11651000.0, "USD"),
                "total_inflated": Quantity(12803550.0, "USD"),
                "depreciable_capital_dcf_inflation_corrected": Quantity(12790800.0, "USD"),
                "initial_equity_depreciable_capital": Quantity(7827969.6, "USD"),
                "annual_initial_equity_depreciable_capital": np.array([4604688.0, 3223281.6, 0.0, 0.0, 0.0]),
                "non_depreciable_capital_dcf_inflation_corrected": Quantity(268821.0, "USD"),
                "annual_non_depreciable_capital": np.array([268821.0, 0.0, 0.0, 0.0, 0.0]),
            },
        }
    ],
    ids=[
        "Realistic case - Capital Cost"
    ]
)

def test_capital_cost_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Capital_Cost_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-7

    assert plugin.direct_inflated.unit["USD"] == pytest.approx(
        expected["direct_inflated"].unit["USD"],
        abs=tolerance
    )

    assert plugin.indirect_inflated.unit["USD"] == pytest.approx(
        expected["indirect_inflated"].unit["USD"],
        abs=tolerance
    )

    assert plugin.depreciable.unit["USD"] == pytest.approx(
        expected["depreciable"].unit["USD"],
        abs=tolerance 
    )

    assert plugin.depreciable_inflated.unit["USD"] == pytest.approx(
        expected["depreciable_inflated"].unit["USD"],
        abs=tolerance
    )

    assert plugin.non_depreciable.unit["USD"] == pytest.approx(
        expected["non_depreciable"].unit["USD"],
        abs=tolerance
    )

    assert plugin.non_depreciable_inflated.unit["USD"] == pytest.approx(
        expected["non_depreciable_inflated"].unit["USD"],
        abs=tolerance
    )   
    
    assert plugin.total.unit["USD"] == pytest.approx(
        expected["total"].unit["USD"],
        abs=tolerance
    )  

    assert plugin.total_inflated.unit["USD"] == pytest.approx(
        expected["total_inflated"].unit["USD"],
        abs=tolerance
    )

    assert plugin.depreciable_capital_dcf_inflation_corrected.unit["USD"] == pytest.approx(
        expected["depreciable_capital_dcf_inflation_corrected"].unit["USD"],
        abs=tolerance
    )

    assert plugin.initial_equity_depreciable_capital.unit["USD"] == pytest.approx(
        expected["initial_equity_depreciable_capital"].unit["USD"],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.annual_initial_equity_depreciable_capital.unit["USD"],
        expected["annual_initial_equity_depreciable_capital"],
        atol=tolerance
    )

    assert plugin.non_depreciable_capital_dcf_inflation_corrected.unit["USD"] == pytest.approx(
        expected["non_depreciable_capital_dcf_inflation_corrected"].unit["USD"],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.annual_non_depreciable_capital.unit["USD"],
        expected["annual_non_depreciable_capital"],
        atol=tolerance
    )