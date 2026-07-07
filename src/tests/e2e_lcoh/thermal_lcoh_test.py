import pytest
from pyH2A.run_pyH2A import pyH2A

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/Thermal_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 3.2705814097046098
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_capital_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 3.7271856030880928
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_labor_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 10.202394944067251
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_production_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 7.35799065042495
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_replacement_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 3.2544152106369704
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_solar_thermal_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 1.6440086736860902
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal/upper_level_files/thermal_variable_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 8.67147418424181
            },
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
    ]
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
    
    result = pyH2A(
       input_data["input_file"], 
        input_data["output_directory"]
    )
    
    # Very strict tolerance to detect economic regression
    tolerance = 1e-13
    
    assert result.base_case.h2_cost == pytest.approx(
        case["expected"]["lcoh"],
        abs=tolerance
    )