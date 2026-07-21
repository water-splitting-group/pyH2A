import pytest
from pyH2A.run_pyH2A import pyH2A

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic_Base.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 185.44329282256822
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/photocatalytic_bases/photocatalytic_catalyst_separation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 99.6855777266403
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/photocatalytic_bases/photocatalytic_hourly_irradiation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 376.5146709131458
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/photocatalytic_bases/photocatalytic_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 184.47274187266245
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/photocatalytic_bases/photocatalytic_photocatalytic_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 642.6546026635854
            },
        },
    ],
    ids=[
        "Photocatalytic_Base",
        "Photocatalytic_Catalyst",
        "Photocatalytic_Hourly",
        "Photocatalytic_Multiple",
        "Photocatalytic_Photocatalytic"
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
    
    assert result.base_case.h2_cost == pytest.approx(
        case["expected"]["lcoh"],
        rel=tolerance
    )