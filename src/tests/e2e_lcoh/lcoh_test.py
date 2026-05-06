import pytest
from pyH2A.run_pyH2A import pyH2A


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 3.2705814128793933/32. # cost per kg of hydrogen / kWh per kg of hydrogen
            },
        },
    ],
    ids=[
        "Thermal_Base",
    ]
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
    
    result = pyH2A(
        input_data["input_file"], 
        input_data["output_directory"]
    )
    
    # Very strict tolerance to detect economic regression
    tolerance = 1e-12
    
    assert result.base_case.final_product_cost == pytest.approx(
        case["expected"]["lcoh"],
        rel=tolerance
    )
