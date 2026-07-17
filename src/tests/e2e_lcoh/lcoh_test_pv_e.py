import pytest
from pyH2A.run_pyH2A import pyH2A


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_Base.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 4.194302976489675},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_battery_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 40.1548227860604},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_electrolyzer_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 6.859428387742992},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_hourly_irradiation_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 17.108717581630824},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_photovoltaic_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 2.657467777523577},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_power_management_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 132.38222070989227},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_reverse_osmosis_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 3.385530136739836},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_stored_power_electrolysis_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 7.397009679328874},
        },
        {
            "input": {
                "input_file": "src/tests/end_to_end/PV_E_bases/pv_e_multiple_modules_test.md",
                "output_directory": "src/tests/end_to_end/",
            },
            "expected": {"lcoh": 4.148928019459272},
        },
    ],
    ids=[
        "PV_E_Base",
        "PV_E_Battery",
        "PV_E_Electrolyzer",
        "PV_E_Hourly_Irradiation",
        "PV_E_Photovoltaic",
        "PV_E_Power_Management",
        "PV_E_Reverse_Osmosis",
        "PV_E_Stored_Power_Electrolysis",
        "PV_E_Multiple_Modules",
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
