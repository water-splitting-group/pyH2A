import pytest
from pyH2A.run_pyH2A import pyH2A

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/Photocatalytic_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 185.44329282256817
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_catalyst_separation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 99.68557772664028
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_hourly_irradiation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 1264.008584330617
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 184.47274187266243
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_photocatalytic_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 642.6546026635854
            },
        },
    ],
    ids=[
        "Photocatalytic_Base_Main",
        "Photocatalytic_Catalyst_separation_plugin",
        "Photocatalytic_Hourly_Irradiation_Plugin",
        "Photocatalytic_Multiple_Modules_Plugin",
        "Photocatalytic_Photocatalytic_plugin",
    ]
)
def test_e2e_lcoh(case):
    """
    End-to-end regression test for Levelized Cost of Hydrogen (LCOH).

    This test runs the full pyH2A workflow using reference Photocatalytic_Base_test.md 
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