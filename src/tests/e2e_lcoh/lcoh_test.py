import pytest
from pyH2A.run_pyH2A import pyH2A


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "data/PV_E/Base/PV_E_Base.md",
                "output_directory": "data/PV_E/Base",
            },
            "expected": {
                "lcoh": 4.194302976489675
            },
        },
        {
            "input": {
                "input_file": "data/PEC/Limit/PEC_Limit.md",
                "output_directory": "data/PEC/Limit",
            },
            "expected": {
                "lcoh": 1.4242951683758598
            },
        },
        {
            "input": {
                "input_file": "data/PEC/No_Conc/PEC_Limit_No_Concentration.md",
                "output_directory": "data/PEC/No_Conc",
            },
            "expected": {
                "lcoh": 15.826371459378658
            },
        },
        {
            "input": {
                "input_file": "data/LCA/PV_E_Base.md",
                "output_directory": ".",
            },
            "expected": {
                "lcoh": 3.5777931317137512
            },
        },
    ],
    ids=[
        "PV_E/Base/PV_E_Base",
        "PEC/Limit/PEC_Limit",
        "No_Conc/PEC_No_Concentration",
        "LCA/PV_E_Base",
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
