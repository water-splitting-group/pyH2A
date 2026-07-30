import pytest
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PEC_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(139.41887561917213, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Photocatalytic_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(185.44329282256822, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(4.194302976489675, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(3.270581409704611, "USD/kg")
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/Thermal_Base_Merge.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": Quantity(3.0993930498121895, "USD/kg")
            },
        },
    ],
    ids=[
        "PEC_Base",
        "Photocatalytic_Base",
        "PV_E_Base",
        "Thermal_Base",
        "Thermal_Base_Merge",
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
    tolerance = 1e-13

    obtained = result.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    expected = case["expected"]["lcoh"].unit['USD/kg']
    
    assert obtained == pytest.approx(
        expected,
        abs=tolerance
    )
