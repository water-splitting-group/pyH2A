import pytest
from pyH2A.run_pyH2A import pyH2A

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/PEC_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 139.41887561917213
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_capital_cost.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 139.8475151386626
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_hourly_irradition.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 131.08137444479016
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_labor_operating_cost.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 139.91796619364624
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_multiple_modules.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 139.06238235169062
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_other_fixed_operating_cost.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 140.3652784598172
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_pec.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 99.35205374520058
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_production.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 127.74642981483795
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_replacement.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 139.57923509057508
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_solar_concentartor.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 173.72124001115256
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/upper_level_files/pec_base_variable_operating_cost.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 179.26310924919397
            },
        },
    ],
    ids=[
        "PEC_Base_Main",
        "PEC_Base_Capital_Cost_Plugin",
        "PEC_Base_Hourly_Irradiation_Plugin",
        "PEC_Base_Labor_Operating_Cost_plugin",
        "PEC_Base_Multiple_Modules_plugin",
        "PEC_Base_Other_Fixed_Operating_Cost_plugin",
        "PEC_Base_PEC_Plugin",
        "PEC_Base_Production_Plugin",
        "PEC_Base_Replacement_Plugin",
        "PEC_Base_Solar_concentrator_Plugin",
        "PEC_Base_Variable_operating_Cost_plugin",
    ]
)
def test_e2e_lcoh(case):
    """
    End-to-end regression test for Levelized Cost of Hydrogen (LCOH).

    This test runs the full pyH2A workflow using reference PEC_Base_test.md 
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
