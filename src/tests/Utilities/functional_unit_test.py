import pytest
from pyH2A.Utilities import functional_unit


TEST_CASES = [
    {
        "input": {
            "Unit of measurement": "kg",
            "Reference": "test",
        },
        "expected": {
            "Functional_Dimension_dot": "mass/time",
            "Functional_Unit_dot": "kg/s",
            "Functional_Unit_per_year": "kg/year",
        },
    },
    {
        "input": {
            "Unit of measurement": "kWh",
            "Reference": "test",
        },
        "expected": {
            "Functional_Dimension_dot": "power",
            "Functional_Unit_dot": "W",
            "Functional_Unit_per_year": "kWh_per_year",
        },
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_set_functional_unit(case):
    functional_unit.set_Functional_Unit(case["input"])

    expected = case["expected"]

    assert functional_unit.Functional_Dimension_dot == expected["Functional_Dimension_dot"]
    assert functional_unit.Functional_Unit_dot == expected["Functional_Unit_dot"]
    assert functional_unit.Functional_Unit_per_year == expected["Functional_Unit_per_year"]