import pytest
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_Electricity_Production_Test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoe": Quantity(0.02858462133297927, "USD/kWh")
            },
        },
    ],
    ids=[
        "PV_E_Electricity_Production_Test",
    ]
)
def test_e2e_lcoe(case):
    """
    End-to-end regression test for Levelized Cost of Electricity (LCOE).

    This test runs the full pyH2A workflow using reference input files
    and asserts that the computed LCOE matches the master-branch
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

    obtained = result.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kWh']
    expected = case["expected"]["lcoe"].unit['USD/kWh']
    
    assert obtained == pytest.approx(
        expected,
        abs=tolerance
    )
