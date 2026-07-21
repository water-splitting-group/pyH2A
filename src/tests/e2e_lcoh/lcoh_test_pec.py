import pytest
from pyH2A.run_pyH2A import pyH2A


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC_Base.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 139.41887561917213},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_capital_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 140.95384791867752},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_hourly_irradition_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 20.241051800889103},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_labor_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 141.24887439224383},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 138.7454994472626},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_other_fixed_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 146.47610701535254},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_pec_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 56.71697140773922},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_production_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 255.09880527921368},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_replacement_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 141.98462716161907},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_solar_concentartor_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 90.07290248911877},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC/pec_variable_operating_cost_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 418.31275217674124},
        },
    ],
    ids=[
        "PEC_Base",
        "PEC_Capital_Cost",
        "PEC_Hourly_Irradiation",
        "PEC_Labor_Operating_Cost",
        "PEC_Multiple_Modules",
        "PEC_Other_Fixed_Operating_Cost",
        "PEC_PEC_Parameters",
        "PEC_Production",
        "PEC_Replacement",
        "PEC_Solar_Concentrator",
        "PEC_Variable_Operating_Cost",
    ],
)
def test_e2e_lcoh(case):
    """
    End-to-end regression test for Levelized Cost of Hydrogen (LCOH).

    This test runs the full pyH2A workflow using reference input files
    and asserts that the computed LCOH matches the master-branch
    reference value within tight numerical tolerance.

    Purpose:
    - Detect unintended economic logic changes
    - Detect numerical drift
    - Protect financial model stability
    """

    input_data = case["input"]

    result = pyH2A(input_data["input_file"], input_data["output_directory"])

    # Very strict tolerance to detect economic regression
    tolerance = 1e-12

    assert result.base_case.h2_cost == pytest.approx(
        case["expected"]["lcoh"], rel=tolerance
    )
