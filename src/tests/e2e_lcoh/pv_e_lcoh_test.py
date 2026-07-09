import pytest
from pyH2A.run_pyH2A import pyH2A

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/PV_E_Base_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 4.194302976489664
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_battery_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 40.1548227860603
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_electrolyzer_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 475.78445553529076
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_hourly_irradiation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 17.10871758163081
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 4.148928019459261
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_photovoltaic_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 2.6574677775235758
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_power_management_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 4.9999263180675255
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_reverse_osmosis_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 3.383515312462802
            },
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E/upper_level_files/pv_e_stored_power_electrolysis_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {
                "lcoh": 272.9310682981415
            },
        },
    ],
    ids=[
        "PV_E_Base_Main",
        "PV_E_Battery_Plugin",
        "PV_E_Electrolyzer_Plugin",
        "PV_E_Hourly_irradiation_Plugin",
        "PV_E_Multiple_Modules_Plugin",
        "PV_E_Photovoltaic_Plugin",
        "PV_E_Power_Management_Plugin",
        "PV_E_Reverse_Osmosis_Plugin",
        "PV_E_Stored_Power_Electrolysis_Plugin",
    ]
)
def test_e2e_lcoh(case):
    """
    End-to-end regression test for Levelized Cost of Hydrogen (LCOH).

    This test runs the full pyH2A workflow using reference PV_E_Base_test.md 
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