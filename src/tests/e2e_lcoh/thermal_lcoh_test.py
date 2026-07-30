import pytest
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/Thermal_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(3.270581409704611, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_capital_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(3.7271856030880977, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_labor_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(10.202394944067255, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_production_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(3.6789953252124796, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_replacement_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(3.2544152106369726, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_solar_thermal_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(1.6440086736860908, "USD/kg")},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_variable_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh":  Quantity(8.671474184241813, "USD/kg")},
        },
    ],
    ids=[
        "Thermal_Base_Main",
        "Thermal_Capital_Cost_Plugin",
        "Thermal_Labor_Operating_Cost_plugin",
        "Thermal_Production_Plugin",
        "Thermal_Replacement_Plugin",
        "Thermal_Solar_Thermal_Plugin",
        "Thermal_Variable_operating_Cost_plugin",
    ],
)
def test_e2e_lcoh(case):
    """
    End-to-end regression test for Levelized Cost of Hydrogen (LCOH).

    This test runs the full pyH2A workflow using reference Thermal_Base_test.md
    and its Upper Level input files and asserts that the computed LCOH
    matches the master-branch reference value within tight numerical tolerance.

    Purpose:
    - Detect unintended economic logic changes
    - Detect numerical drift
    - Protect financial model stability
    """

    input_data = case["input"]

    result = pyH2A(input_data["input_file"], input_data["output_directory"])

    # Very strict tolerance to detect economic regression
    tolerance = 1e-13

    obtained = result.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    expected = case["expected"]["lcoh"].unit['USD/kg']
    
    assert obtained == pytest.approx(
        expected,
        abs=tolerance
    )
