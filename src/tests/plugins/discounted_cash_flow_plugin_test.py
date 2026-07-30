import pytest
import numpy as np

from pyH2A.Plugins.Core.Discounted_Cash_Flow_Plugin import Discounted_Cash_Flow_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

from tests.Utilities.check_dicts_for_testing import check_dicts

class DummyDCF:
    """Minimal DCF object for Discounted_Cash_Flow_Plugin with configurable inputs.

    Mirrors the pre-computed outputs that `Capital_Cost_Plugin`, `Replacement_Plugin`,
    `Other_Fixed_Operating_Cost_Plugin` and `Variable_Operating_Cost_Plugin` insert into
    `dcf.inp`, since `Discounted_Cash_Flow_Plugin` only consumes already-processed values.
    """

    def __init__(
        self,
        plant_years_relative,
        analysis_years_ones,
        construction_years_ones,
        start_index,
        output_at_gate,
        inflation_factor_full,
        inflation_correction,
        financial_input_values,
        annual_equity_depreciable_capital,
        initial_equity_depreciable_capital,
        depreciable_capital_inflation_corrected,
        annual_non_depreciable_capital,
        non_depreciable_capital_inflation_corrected,
        annual_replacement_costs,
        annual_fixed_operating_costs,
        annual_variable_operating_costs,
    ):
        self.functional_unit = resolve_functional_unit('kg')  # Set a default functional unit for testing
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {
                        "Plant years relative": plant_years_relative,
                        "Analysis years ones": analysis_years_ones,
                        "Construction years ones": construction_years_ones,
                        "Start index": start_index,
                    },
                    "Unit": "-",
                    "Processed": "Yes",
                },
            },
            "Technical Operating Parameters and Specifications": {
                "Output at gate by year": {
                    "Value": output_at_gate,
                    "Unit": "kg",
                    "Processed": "Yes",
                },
            },
            "Inflation": {
                "Inflation factor full": {
                    "Value": inflation_factor_full,
                    "Unit": "-",
                    "Processed": "Yes",
                },
                "Inflation correction": {
                    "Value": inflation_correction,
                    "Unit": "-",
                },
            },
            "Financial Input Values": {
                key: {"Value": value["Value"],
                      "Unit": value["Unit"]
                      }
                for key, value in financial_input_values.items()
            },
            "Depreciable Capital Costs": {
                "Annual equity": {
                    "Value": annual_equity_depreciable_capital,
                    "Unit": "USD",
                    "Processed": "Yes",
                },
                "Initial equity": {
                    "Value": initial_equity_depreciable_capital,
                    "Unit": "USD",
                },
                "Inflation corrected": {
                    "Value": depreciable_capital_inflation_corrected,
                    "Unit": "USD",
                },
            },
            "Non-Depreciable Capital Costs": {
                "Annual": {
                    "Value": annual_non_depreciable_capital,
                    "Unit": "USD",
                    "Processed": "Yes",
                },
                "Inflation corrected": {
                    "Value": non_depreciable_capital_inflation_corrected,
                    "Unit": "USD",
                },
            },
            "Replacement": {
                "Total": {
                    "Value": annual_replacement_costs,
                    "Unit": "USD",
                    "Processed": "Yes",
                },
            },
            "Fixed Operating Costs": {
                "Annual": {
                    "Value": annual_fixed_operating_costs,
                    "Unit": "USD",
                    "Processed": "Yes",
                },
            },
            "Variable Operating Costs": {
                "Annual": {
                    "Value": annual_variable_operating_costs,
                    "Unit": "USD",
                    "Processed": "Yes",
                },
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_years_relative": np.arange(-2, 5),
                "analysis_years_ones": np.ones(7),
                "construction_years_ones": np.ones(2),
                "start_index": 2,
                "output_at_gate": np.array([100_000.0, 100_000.0, 100_000.0, 100_000.0, 100_000.0]),
                # Must equal (1 + Inflation rate) ** plant_years_relative for the levelized cost
                # formula's break-even identity (NPV of after-tax cash flow == 0) to hold; an
                # inflation factor array that is inconsistent with "Inflation rate" and
                # "plant_years_relative" triggers the plugin's internal NPV sanity check.
                "inflation_factor_full": (1 + 0.02) ** np.arange(-2, 5),
                "inflation_correction": 1.01,
                "financial_input_values": {
                    "Fraction equity financing": {
                        "Value": 0.6, 
                        "Unit": "-"},
                    "Interest rate on debt": {
                        "Value": 0.05, 
                        "Unit": "-"},
                    "Depreciation schedule length": {
                        "Value": 5,
                        "Unit": "year"},
                    "After-tax real IRR": {
                        "Value": 0.08,
                        "Unit": "-"},
                    "Inflation rate": {
                        "Value": 0.02,
                        "Unit": "-"},
                    "Federal taxes": {
                        "Value": 0.21,
                        "Unit": "-"},
                    "State taxes": {
                        "Value": 0.06, 
                        "Unit": "-"},
                    "Start-up time": {
                        "Value": 1, 
                        "Unit": "year"},
                    "Fraction of revenues during start-up": {
                        "Value": 0.75, 
                        "Unit": "-"},
                    "Decommissioning costs (fraction of depreciable capital investment)": {
                        "Value": 0.10,
                        "Unit": "-"},
                    "Salvage value (fraction of total capital investment)": {
                        "Value": 0.10,
                        "Unit": "-"},
                    "Working Capital (fraction of yearly change in operating costs)": {
                        "Value": 0.15, 
                        "Unit": "-"},
                },
                "annual_equity_depreciable_capital": np.array(
                    [400_000.0, 300_000.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                ),
                "initial_equity_depreciable_capital": 700_000.0,
                "depreciable_capital_inflation_corrected": 750_000.0,
                "annual_non_depreciable_capital": np.array(
                    [50_000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                ),
                "non_depreciable_capital_inflation_corrected": 55_000.0,
                "annual_replacement_costs": np.array(
                    [0.0, 0.0, 5_000.0, 0.0, 6_000.0, 0.0, 7_000.0]
                ),
                "annual_fixed_operating_costs": np.array(
                    [0.0, 0.0, 80_000.0, 82_000.0, 84_000.0, 86_000.0, 88_000.0]
                ),
                "annual_variable_operating_costs": np.array(
                    [0.0, 0.0, 40_000.0, 41_000.0, 42_000.0, 43_000.0, 44_000.0]
                ),
            },
            "expected": {
                "npv_dict": {
                    "initial_equity_depreciable_capital": 672331.1546840959,
                    "non_depreciable_capital_costs": 50000.0,
                    "replacement_costs": 12111.568512247086,
                    "fixed_operating_costs": 286559.0307023404,
                    "variable_operating_costs": 143279.5153511702,
                    "salvage": 48758.79946567656,
                    "decommissioning": 45427.4529183322,
                    "working_capital_reserve": 4924.708101634298,
                    "interest": 76916.31210392262,
                    "principal_payment": 161353.11262835842,
                    "depreciation_charge": 705126.1558786422,
                    "product_sales": 348261.90329598176,
                    "revenue": 1471940.97916082,
                    "pre_depreciation_income": 968517.4675507309,
                    "taxable_income": 263391.3116720886,
                    "taxes": 67796.9236243956,
                    "after_tax_income": 900720.5439263353,
                },
                "contributions": {
                    'Table Group': 'Total Cost of Product',
                    'Total': Quantity(4.353749092037852, 'USD/kg'),
                    'Data': {
                        "Initial equity depreciable capital": Quantity(1.9886403026318826, 'USD/kg'),
                        "Non depreciable capital": Quantity(0.14789142885742612, 'USD/kg'),
                        "Replacement costs": Quantity(0.03582394345961665, 'USD/kg'),
                        "Salvage": Quantity(-0.14422017044703225, 'USD/kg'),
                        "Decommissioning": Quantity(0.134366618428912, 'USD/kg'),
                        "Fixed operating costs": Quantity(0.8475924900513634, 'USD/kg'),
                        "Variable operating costs": Quantity(0.4237962450256817, 'USD/kg'),
                        "Working capital reserve": Quantity(0.014566442357128779, 'USD/kg'),
                        "Interest": Quantity(0.22750526598985715, 'USD/kg'),
                        "Principal payment": Quantity(0.4772548475440227, 'USD/kg'),
                        "Taxes": Quantity(0.20053167813899309, 'USD/kg'),
                        }
                },
            },
        }
    ],
)
def test_discounted_cash_flow_plugin(case):
    """Check plugin combines pre-computed cost/revenue inputs into the correct levelized
    cost of product, net present values, and cost contributions."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Discounted_Cash_Flow_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    check_dicts(plugin.npv_dict, expected["npv_dict"], tolerance=tolerance)
    check_dicts(plugin.contributions, expected["contributions"], tolerance=tolerance)