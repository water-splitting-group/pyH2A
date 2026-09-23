import pytest
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh":  Quantity(185.44329282256822, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_catalyst_separation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(99.6855777266403, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_hourly_irradiation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(376.5146709131457, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(184.47274187266245, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic/upper_level_files/photocatalytic_photocatalytic_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(642.6546026635854, "USD/kg")
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

    obtained = result.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    expected = case["expected"]["lcoh"].unit['USD/kg']
    
    assert obtained == pytest.approx(
        expected,
        abs=tolerance
    )
